from Acquisition import aq_chain, aq_base
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import safe_unicode
from datetime import datetime, timedelta
from plone.registry.interfaces import IRegistry
from urlparse import urlparse
from zope.annotation.interfaces import IAnnotations
from zope.component import subscribers, getAdapters, getUtility
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.schema.interfaces import IVocabularyFactory
from zope.interface import Interface

from agsci.api.interfaces import IAPIDataAdapter
from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DEFAULT_TIMEZONE, DELIMITER
from agsci.atlas.decorators import context_memoize
from agsci.atlas.interfaces import ILocationMarker
from agsci.atlas.utilities import ploneify, truncate_text, SitePeople, \
                                  isInternalStore, isExternalStore, localize

from agsci.leadimage.interfaces import ILeadImageMarker as ILeadImage

from .error import HighError, MediumError, LowError, NoError, ManualCheckError
from .. import IAtlasProduct
from ..adapters import EventGroupDataAdapter
from ..behaviors import IAtlasPersonCategoryMetadata
from ..event import IEvent
from ..event.cvent import ICventEvent
from ..event.group import IEventGroup
from ..video import IVideo
from ..vocabulary import CurriculumVocabularyFactory
from ..vocabulary.calculator import AtlasMetadataCalculator, ExtensionMetadataCalculator

import pickle
import pytz
import re
import redis
import requests

alphanumeric_re = re.compile("[^A-Za-z0-9]+", re.I|re.M)

# Cached version of _getIgnoreChecks
def getIgnoreChecks(context):

    request = getRequest()

    key = "ignore-checks-%s" % context.UID()

    cache = IAnnotations(request)

    data = cache.get(key, None)

    if not isinstance(data, list):
        data = _getIgnoreChecks(context)
        cache[key] = data

    return data

def _getIgnoreChecks(context):

    for o in context.aq_chain:

        if IPloneSiteRoot.providedBy(o):
            break

        ignore_checks = getattr(o.aq_base, 'ignore_checks', [])

        if ignore_checks:
            return ignore_checks

    return []

# Cache errors on HTTP Request, since we may be calling this multiple times.
# Ref: http://docs.plone.org/manage/deploying/performance/decorators.html#id7
def getValidationErrors(context):

    request = getRequest()

    key = "product-validation-errors-%s" % context.UID()

    cache = IAnnotations(request)

    data = cache.get(key, None)

    if not isinstance(data, list):
        data = _getValidationErrors(context)
        cache[key] = data

    return data

def _getValidationErrors(context):

    errors = []
    levels = [
        x.level for x in (
            HighError,
            MediumError,
            LowError,
            ManualCheckError,
            NoError,
        )
    ]

    ignore_checks = getIgnoreChecks(context)

    for i in subscribers((context,), IContentCheck):

        if i.error_code not in ignore_checks:

            try:
                for j in i:

                    # NoError is a NOOP error. Ignore.
                    if not isinstance(j, NoError):
                        errors.append(j)

            except Exception as e:
                errors.append(
                    LowError(i, u"Internal error running check: '%s: %s'" % (e.__class__.__name__, e.message))
                )

    # Sort first on the hardcoded order
    errors.sort(key=lambda x: x.sort_order)

    # Then sort on the severity
    errors.sort(key=lambda x: levels.index(x.level))

    return errors


# Interface for warning subscribers
class IContentCheck(Interface):
    pass


# Base class for content check
class ContentCheck(object):

    # Title for the check
    title = "Default Check"

    # Description for the check
    description = ""

    # Action to remediate the issue
    action =""

    # Render the output as HTML.
    render = False

    # Render the action output as HTML
    render_action = False

    # Sort order (lower is higher)
    sort_order = 0

    # Redis cache key
    redis_cachekey = u""

    # Timeout for cache
    CACHED_DATA_TIMEOUT = 600 # Ten minutes

    @property
    def redis(self):
        return redis.StrictRedis(host='localhost', port=6379, db=0)

    def __init__(self, context):
        self.context = context

    @property
    def registry(self):
        return getUtility(IRegistry)

    @property
    def error_code(self):
        return self.__class__.__name__

    @property
    def request(self):
        return getRequest()

    def value(self):
        """ Returns the value of the attribute being checked """

    def check(self):
        """ Performs the check and returns HighError/MediumError/LowError/None """

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def wftool(self):
        return getToolByName(self.context, 'portal_workflow')

    @property
    def portal_transforms(self):
        return getToolByName(self.context, 'portal_transforms')

    @property
    def review_state(self):
        return self.wftool.getInfoFor(self.context, 'review_state')

    def __iter__(self):
        return self.check()

    # Returns an object with the keyword arguments as properties
    def object_factory(self, **kwargs):
        from agsci.atlas import object_factory as _
        return _(**kwargs)

    @property
    def isPerson(self):
        return IAtlasPersonCategoryMetadata.providedBy(self.context)

    @property
    def isChildProduct(self):

        # Doing this import in the method, since it's a circular import on
        # startup if we don't.
        from agsci.atlas.indexer import IsChildProduct

        child_product = IsChildProduct(self.context)

        return not not child_product()

    @property
    def isVideo(self):
        return IVideo.providedBy(self.context)

    @property
    def isInternalStore(self):
        return isInternalStore(self.context)

    @property
    def isExternalStore(self):
        return isExternalStore(self.context)

    @property
    def now(self):
        return datetime.now(pytz.timezone(DEFAULT_TIMEZONE))

# Validates the product title length
class TitleLength(ContentCheck):

    title = "Product Title Length"
    description = "Titles should be no more than 60 characters."
    action = "Edit the title to be no more than 60 characters.  For short titles, add more detail."

    # Sort order (lower is higher)
    sort_order = 1

    def value(self):
        return len(self.context.title)

    def check(self):
        v = self.value()

        if v > 128:
            yield HighError(self, u"%d characters is too long." % v)
        elif v > 80:
            yield MediumError(self, u"%d characters is too long." % v)
        elif v > 60:
            yield LowError(self, u"%d characters is too long." % v)
        elif v < 16:
            yield LowError(self, u"%d characters may be too short." % v)


# Validates the product description length
class DescriptionLength(ContentCheck):

    low_limit = 200
    medium_limit = 250
    high_limit = 280

    title = "Product Description Length"
    description = "Product must have a description, which should be a maximum of %d characters." % low_limit
    action = "Edit the description to be no more than %d characters.  For short or missing descriptions, add more detail." % low_limit

    # Sort order (lower is higher)
    sort_order = 1

    def value(self):
        if hasattr(self.context, 'description'):
            if isinstance(self.context.description, (str, unicode)):
                return len(self.context.description)

        return 0

    def check(self):

        # Child products do not require descriptions.
        if not self.isChildProduct:

            v = self.value()

            if v > self.high_limit:
                yield HighError(self, u"%d characters is too long." % v)
            elif v > self.medium_limit:
                yield MediumError(self, u"%d characters is too long." % v)
            elif v > self.low_limit:
                yield LowError(self, u"%d characters is too long." % v)
            elif v == 0:
                yield HighError(self, u"A description is required for this product.")
            elif v < 32:
                yield LowError(self, u"%d characters may be too short." % v)

# ConditionalCheck: Determines error level to return for checks that may
# be run on Person products, or other products.  Returns High for other products,
# Low for Person products, but NoError for Person Products who are not Educators
# or Faculty.
class ConditionalCheck(ContentCheck):

    @property
    def valid_classifications(self):

        vocab = getUtility(IVocabularyFactory, "agsci.person.classifications")

        values = vocab(self.context)

        return [x.value for x in values]

    @property
    def classifications(self):

        if self.isPerson:

            c = getattr(self.context, 'classifications', [])

            if c and isinstance(c, (list, tuple)):
                return list(set(c) & set(self.valid_classifications))

        return []

    @property
    def isEducatorFaculty(self):

        if self.isPerson:

            check_classifications = (u'Faculty', u'Educators')

            return set(check_classifications) & set(self.classifications)

        return False

    # Level of error to return
    @property
    def error(self):

        # Check if we're a person
        if self.isPerson:

            # Must be Educator or Faculty for team check
            if not self.isEducatorFaculty:
                return NoError

            return LowError

        return HighError

# Validates that the right number of EPAS categories are selected
# Parent class with basic logic
class _ProductEPAS(ContentCheck):

    @property
    def error(self):
        return ConditionalCheck(self.context).error

    title = "EPAS Selections"
    fields = ('atlas_state_extension_team', 'atlas_program_team', 'atlas_curriculum')
    action = "Under the 'Categorization' tab, select the appropriate EPAS information"

    @property
    def description(self):
        return '%s products should have one each of State Extension Team, Program Team, and Curriculum selected.' % self.context.Type()

    # Sort order (lower is higher)
    sort_order = 3

    # Maximum number of curriculums
    max_curriculums = 1

    # This generates all valid possibilities for counts of curriculums.
    # The assumption is that (due to the structure of the data) we will never
    # have a larger number at a higher level.
    @property
    def required_values(self):
        v = []

        max_range = self.max_curriculums + 1

        for i in range(1,max_range):
            for j in range(1,max_range):
                for k in range(1,max_range):
                    v.append(
                        tuple(
                            sorted([i,j,k])
                        )
                    )

        v = list(set(v))

        return v

    # Number of selections for each field.
    def value(self):
        try:
            return tuple([len(getattr(self.context, x, [])) for x in self.fields])
        except TypeError:
            return (0,0,0)

    def check(self):
        v = self.value()

        if v not in self.required_values:
            yield self.error(self, u"Number of selections incorrect.")


# Validates that the right number of EPAS categories are selected

class _WorkshopGroupEPAS(_ProductEPAS):

    max_curriculums = 3

    @property
    def description(self):
        return '%s products should have at least one (and up to three) State Extension Teams, Program Teams, and Curriculums selected.' % self.context.Type()


class _WebinarGroupEPAS(_WorkshopGroupEPAS):

    pass


class _OnlineCourseGroupEPAS(_ProductEPAS):

    pass


class _EPASLevelValidation(ContentCheck):

    @property
    def error(self):
        return ConditionalCheck(self.context).error

    # Sort order (lower is higher)
    sort_order = 2

    epas_titles = {
        'atlas_state_extension_team': 'State Extension Team',
        'atlas_program_team': 'Program Team',
        'atlas_curriculum': 'Curriculum'
    }

    epas_indexes = {
        'atlas_state_extension_team': 'StateExtensionTeam',
        'atlas_program_team': 'ProgramTeam',
    }

    epas_levels = ['atlas_state_extension_team', 'atlas_program_team']

    @property
    def title(self):
        return "EPAS %s" % self.field_title

    @property
    def field_title(self):
        return self.epas_titles.get(self.epas_levels[-1])

    @property
    def description(self):
        return "%s should be assigned when available." % self.title

    @property
    def action(self):
        return "Under the 'Categorization' tab, select the appropriate %s." % self.title

    def value(self):
        # Get the category level values
        v1 = getattr(self.context, self.epas_levels[0] , [])
        v2 = getattr(self.context, self.epas_levels[1], [])

        # Make these lists if they were None values
        if not v1:
            v1 = []

        if not v2:
            v2 = []

        return (v1, v2)

    # The vocabulary for the second level
    @property
    def vocabulary(self):
        mc = ExtensionMetadataCalculator(self.epas_indexes[self.epas_levels[1]])

        return mc.getTermsForType()

    # All potential options for the second level vocabulary
    def options(self):
        try:
            return [x.value for x in self.vocabulary]
        except:
            return []

    def check(self):
        # Get the level 1 and level 2 values
        (v1, v2) = self.value()

        # Iterate through the level 1 values.  If a level 2 value is available
        # for that level 1, but no level 2s are selected, throw an error
        options = self.options()

        for i in v1:

            available_v2 = [x for x in options if x.startswith('%s%s' % (i, DELIMITER))]

            if available_v2:
                if not (set(v2) & set(available_v2)):

                    yield self.error(self, (u"Values for '%s' under %s '%s' are " +
                                           u"available, but not selected.") %
                                              (self.field_title,
                                               self.epas_titles.get(self.epas_levels[0]),
                                               i))

class _EPASProgramTeamValidation(_EPASLevelValidation):
    pass

class _EPASCurriculumValidation(_EPASLevelValidation):

    # Level of error to return
    @property
    def error(self):

        c = ConditionalCheck(self.context)

        if c.isPerson:
            return NoError

        return HighError

    epas_levels = ['atlas_program_team', 'atlas_curriculum', ]

    @property
    def vocabulary(self):
        return CurriculumVocabularyFactory(self.context)


class ProductCategoryValidation(ContentCheck):

    # Sort order (lower is higher)
    sort_order = 2

    category_fields = [1, 2]

    @property
    def error(self):
        return ConditionalCheck(self.context).error

    @property
    def title(self):
        return "Category Level %d" % self.category_fields[-1]

    @property
    def description(self):
        return "%s should be assigned when available." % self.title

    action = "Under the 'Categorization' tab, select the appropriate Categories."

    def value(self):
        # Get the category level values
        v1 = getattr(self.context, 'atlas_category_level_%d' % self.category_fields[0] , [])
        v2 = getattr(self.context, 'atlas_category_level_%d' % self.category_fields[1], [])

        return (v1, v2)

    def check(self):
        # Get the level 1 and level 2 values
        (v1, v2) = self.value()

        # Iterate through the level 1 values.  If a level 2 value is available
        # for that level 1, but no level 1s are selected, throw an error
        mc = AtlasMetadataCalculator('CategoryLevel%d' % self.category_fields[1])
        vocabulary = mc.getTermsForType()

        for i in v1:

            available_v2 = [x.value for x in vocabulary._terms if x.value.startswith('%s%s' % (i, DELIMITER))]

            if available_v2:
                if not (set(v2) & set(available_v2)):

                    yield self.error(self, (u"Values for Category Level %d '%s' " +
                                     u"are available, but not selected. Best practice " +
                                     u"is to select all levels of categories where " +
                                     u"options are available.") % (self.category_fields[1], i))


# Validates that a Category Level 1 is selected for all.
class ProductCategory1(ProductCategoryValidation):

    category_fields = [1,]

    title = "Category Level %d" % category_fields[-1]
    description = "%s should be assigned." % title

    def value(self):
        return getattr(self.context, 'atlas_category_level_%d' % self.category_fields[0] , [])

    def check(self):
        # Get the level 1 and level 1 values
        v1 = self.value()

        if not v1:
            yield self.error(self, u"%s products should have a Category Level 1." % self.context.Type())


# Validates that a Category Level 2 is selected for all Category Level 1's
# that are available.
class ProductCategory2(ProductCategoryValidation):

    pass


# Validates that a Category Level 3 is selected for all Category Level 2's
# that are available.
class ProductCategory3(ProductCategoryValidation):

    category_fields = [2, 3]

    # Level of error to return
    @property
    def error(self):

        c = ConditionalCheck(self.context)

        if c.isPerson:
            return NoError

        return HighError

# Check for over-categorized products
class ProductCategoryCount(ContentCheck):

    # Title for the check
    title = "Category Count"

    # Description for the check
    description = "Categories should be limited to a few that are relevant to the product."

    # Action to take
    action = "Ensure that all categories are needed. If too many categories are selected, this product may show up in too many places."

    # Limits for levels 1..3
    limits = (3, 8, 10)

    # Number of levels
    @property
    def levels(self):
        return len(self.limits)

    def value(self):

        v = []

        for i in range(0, self.levels):

            level = i + 1
            field = 'atlas_category_level_%d' % level
            value = getattr(self.context, field, [])

            if not isinstance(value, (tuple, list)):
                value = []

            v.append(len(value))

        return v

    def check(self):

        value = self.value()

        for i in range(0, self.levels):

            if value[i] > self.limits[i]:

                level = i + 1

                yield LowError(self, "Category Level %d has %d values selected." % (level, value[i]))

class ProductAttributeCount(ContentCheck):

    # Title for the check
    title = "Attribute Count"

    # Description for the check
    description = "Attributes should be limited to a few that are relevant to the product."

    # Action to take
    action = "Ensure that all attributes are needed. If too many attributes are selected, this product may show up in too many places."

    # Limit
    limit = 10

    # Ignore these attribute fields
    ignore_fields = ['atlas_language',]

    @property
    def fields(self):
        from agsci.atlas.browser.views.report.status import AtlasContentStatusView
        v = AtlasContentStatusView(self.context, self.request)
        return v.filter_fields

    def value(self):

        _ = []

        for f in self.fields:

            if f in self.ignore_fields:
                continue

            v = getattr(aq_base(self.context), f, [])

            if v and isinstance(v, (list, tuple)):
                _.extend(v)

        return _

    def check(self):

        v = len(self.value())

        if v > self.limit:
            yield LowError(self, u"Product has %d attributes (> %d) assigned ." % (v, self.limit))

# Checks for issues in the text.  This doesn't actually check, but is a parent
# class for other checks.
class BodyTextCheck(ContentCheck):

    # Title for the check
    title = "HTML: Body Text Check"

    # Description for the check
    description = ""

    # Sort order (lower is higher)
    sort_order = 10

    # h1 - h6
    all_heading_tags = ['h%d' % x for x in range(1,7)]

    resolveuid_re = re.compile("resolveuid/([abcdef0-9]{32})", re.I|re.M)

    @property
    def internal_link_uids(self):

        _ = []

        for a in self.getLinks():

            href = a.get('href', '')

            if href:

                m = self.resolveuid_re.match(href)

                if m:
                    _.append(m.group(1))
        return _

    @property
    def internal_image_uids(self):

        _ = []

        for a in self.getImages():

            href = a.get('src', '')

            if href:

                m = self.resolveuid_re.match(href)

                if m:
                    _.append(m.group(1))
        return _

    @property
    def contents(self):

        # Get API adapters (since they have the getPages() method)
        for (name, adapted) in getAdapters((self.context,), IAPIDataAdapter):
            if hasattr(adapted, 'getPages'):
                return adapted.getPages()

        return []

    def getHTML(self, o):
        if hasattr(o, 'text') and hasattr(o.text, 'raw'):
            if o.text.raw:
                return safe_unicode(o.text.raw)

        return ''

    def html_to_text(self, html):
        text = self.portal_transforms.convert('html_to_text', html).getData()
        text = " ".join(text.strip().split())
        return safe_unicode(text)

    def soup_to_text(self, soup):
        html = safe_unicode(repr(soup))
        text = self.portal_transforms.convert('html_to_text', html).getData()
        text = " ".join(text.strip().split())
        return safe_unicode(text)

    def value(self):
        return self.html

    @property
    @context_memoize
    def soup(self):
        return BeautifulSoup(self.html)

    @property
    @context_memoize
    def html(self):
        v = [
            self.getHTML(self.context)
        ]

        for o in self.contents:
            v.append(self.getHTML(o))

        v = ' '.join(v)

        return safe_unicode(v)

    @property
    @context_memoize
    def text(self):
        return self.html_to_text(self.html)

    def toWords(self, text):
        text = text.lower()
        text = text.replace('@psu.edu', '__PENN_STATE_EMAIL_ADDRESS_DOMAIN__')
        text = alphanumeric_re.sub(' ', text).split()
        return list(set(text))

    @property
    def words(self):
        return self.toWords(self.text)

    def check(self):
        pass

    def getLinks(self):
        return self.soup.findAll('a')

    def getImages(self):
        return self.soup.findAll('img')

    def getHeadings(self):
        return self.soup.findAll(self.all_heading_tags)

    @property
    @context_memoize
    def uid_to_brain(self):
        return dict([(x.UID, x) for x in self.portal_catalog.searchResults()])


# Checks for appropriate heading level hierarchy, e.g. h2 -> h3 -> h4
class BodyHeadingCheck(BodyTextCheck):

    def value(self):
        return self.getHeadings()

# Generic Image check that returns all <img> tags as the value()
class BodyImageCheck(BodyTextCheck):

    def value(self):
        return self.soup.findAll('img')


# Generic Image check that returns all <img> tags as the value()
class BodyLinkCheck(BodyTextCheck):

    bad_domains = []
    ok_urls = []

    def parse_url(self, url, strip_slash=False):
        parsed_url = urlparse(url)

        domain = parsed_url.netloc
        path = parsed_url.path
        scheme = parsed_url.scheme

        if strip_slash:
            if path.endswith('/'):
                path = path[:-1]

        return (scheme, domain, path)

    def url_equivalent(self, url_1, url_2, match_protocol=True):

        (scheme_1, domain_1, path_1) = self.parse_url(url_1, strip_slash=True)
        (scheme_2, domain_2, path_2) = self.parse_url(url_2, strip_slash=True)

        (_scheme, _domain, _path) = (
            scheme_1==scheme_2,
            domain_1==domain_2,
            path_1==path_2,
        )

        if match_protocol:
            return _scheme and _domain and _path

        return _domain and _path

    def value(self):
        return self.soup.findAll('a')

    def is_bad_url(self, url):

        if url:

            (scheme, domain, path) = self.parse_url(url)

            # Handle no-domain cases
            if not domain:

                # Mailto is fine
                if scheme == 'mailto':
                    return False

                # URLs with 'resolveuid' are OK
                if path.startswith('resolveuid'):
                    return False

                # Otherwise, URLs should have a domain
                return True

            # Check for 'bad' domains
            elif domain in self.bad_domains:

                # If our domain/path is in the `ok_urls` list, it's an exception.
                for (_d, _p) in self.ok_urls:

                    if domain == _d and path.startswith(_p):
                        return False

                return True

# Checks for appropriate heading level hierarchy, e.g. h2 -> h3 -> h4
class HeadingLevels(BodyHeadingCheck):

    # Title for the check
    title = "HTML: Heading Levels"

    # Description for the check
    description = "Validates that the heading level hierarchy is correct."

    # Remedial Action
    action = "In the product text (including any pages for Articles), validate that the heading levels are in the correct order, and none are skipped."

    def check(self):

        headings = self.value()

        # Get heading tag object names (e.g. 'h2')
        heading_tags = [x.name for x in headings]

        # If no heading tags to check, return
        if not heading_tags:
            return

        # Check if we have an h1 (not permitted)
        if 'h1' in heading_tags:
            yield MediumError(self, "An <h1> heading is not permitted in the body text.")

        # Validate that the first tag in the listing is an h2
        if heading_tags[0] != 'h2':
            yield MediumError(self, "The first heading in the body text must be an <h2>.")

        # Check for heading tag order, and ensure we don't skip any
        for i in range(0, len(heading_tags)-1):
            this_heading = heading_tags[i]
            next_heading = heading_tags[i+1]

            this_heading_idx = self.all_heading_tags.index(this_heading)
            next_heading_idx = self.all_heading_tags.index(next_heading)

            if next_heading_idx > this_heading_idx and next_heading_idx != this_heading_idx + 1:
                heading_tag_string = "<%s> to <%s>" % (this_heading, next_heading) # For error message
                yield MediumError(self, "Heading levels in the body text are skipped or out of order: %s" % heading_tag_string)


# Check for heading length
class HeadingLength(BodyHeadingCheck):

    # Title for the check
    title = "HTML: Heading Text Length"

    # Description for the check
    description = "Validates that the heading text is not too long. "

    # Remedial Action
    action = "Ensure that headings are a maximum of 120 characters, and ideally 60 characters or less."

    # Warning levels for h2 and h3.  Allow h3's to be slightly longer before a warning is triggered.
    warning_levels = {
                        'h2' : 60,
                        'h3' : 100,
    }

    def check(self):
        headings = self.getHeadings()

        for i in headings:
            text = self.soup_to_text(i)
            warning_length = self.warning_levels.get(i.name, 99999)

            v = len(text)

            if v > 200:
                yield HighError(self, u"Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > 120:
                yield MediumError(self, u"Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > warning_length:
                yield LowError(self, u"Length of %d characters for <%s> heading '%s' may be too long." % (v, i.name, text))


# Verifies that the product title is unique for that type of product
class ProductUniqueTitle(ContentCheck):

    # Title for the check
    title = "Unique Product Title"

    # Description for the check
    description = "Validates that the product title is unique within a product type."

    action = "Add additional context to the title, or combine multiple related articles."

    # Sort order (lower is higher)
    sort_order = 4

    # Render the output as HTML.
    render = True

    def value(self):

        # Query catalog for all objects of the same type
        results = self.portal_catalog.searchResults({'Type' : self.context.Type(),
                                                     'review_state' :  ACTIVE_REVIEW_STATES})

        # Removes the entry for this product
        results = filter(lambda x: x.UID != self.context.UID(), results)

        # Find titles that exactly match.
        results = filter(lambda x: safe_unicode(x.Title.strip().lower()) == safe_unicode(self.context.title.strip().lower()), results)

        # Returns the rest of the matching brains
        return results

    def check(self):
        value = self.value()
        if value:
            urls = u"<ul>%s</ul>" % u" ".join([u"<li><a href='%s'>%s</a></li>" % (x.getURL(), safe_unicode(x.Title)) for x in value])
            yield MediumError(self, u"%s(s) with a duplicate title found at: %s" % (self.context.Type(), urls))


# Verifies that the product owner is a valid person in the directory.
class ProductValidOwners(ContentCheck):

    # Title for the check
    title = "Valid Owner(s)"

    # Description for the check
    description = "Validates that the owner id(s) are active individuals in the directory"

    action = "Under the 'Ownership' tab, ensure that all of the ids listed in the 'Owners' field are Active in the directory"

    # Only show active people
    active = True

    # Sort order (lower is higher)
    sort_order = 5

    def value(self):
        # Get the owners
        owners = getattr(self.context, 'owners', [])

        # Filter out blank owners
        return [x for x in owners if x]

    def validPeopleIds(self):

        sp = SitePeople(active=self.active)
        return sp.getValidPeopleIds()

    def invalidPeopleIds(self):
        # Get the owners, and the valid users
        value = set(self.value())
        user_ids = set(self.validPeopleIds())

        # Find any invalid users
        return list(value - user_ids)

    def check(self):

        # Find any invalid users
        invalid_user_ids = self.invalidPeopleIds()

        # Raise a warning if invalid users are found.
        if invalid_user_ids:
            invalid_user_ids = ", ".join(invalid_user_ids)
            yield MediumError(self, u"User id(s) '%s' are invalid." % invalid_user_ids)

# Verifies that the product authors are valid people in the directory.
class ProductValidAuthors(ProductValidOwners):

    # Title for the check
    title = "Valid Author(s)"

    # Description for the check
    description = "Validates that the author id(s) are active individuals in the directory"

    action = "Under the 'Ownership' tab, ensure that all of the ids listed in the 'Author' field are either Active or Inactive in the directory."

    # Show active and inactive people
    active = False

    # Sort order (lower is higher)
    sort_order = 5

    def value(self):
        # Get the authors
        authors = getattr(self.context, 'authors', [])

        if authors:
            # Filter out blank owners
            return [x for x in authors if x]

        return []

# Validate that either internal or external authors are configured
class ProductHasAuthors(ContentCheck):

    # Title for the check
    title = "Has Authors/Instructors/Speakers"

    # Description for the check
    description = "Verifies that this product has internal or external authors/instructors/or speakers populated."

    action = "Under the 'Ownership' tab, ensure that there are either current Penn State ids in the 'Authors' field, or author information in the 'External Authors' field."

    def value(self):
        # Get the authors
        authors = getattr(self.context, 'authors', [])
        external_authors = getattr(self.context, 'external_authors', [])

        return (authors or external_authors)

    def check(self):

        if not self.value():
            yield LowError(self, 'No authors or external authors listed.')

# Checks for embedded videos (iframe, embed, object, etc.) in the text.
# Raises a High if there's a YouTube or Vimeo video (specifically) or a
# Low otherwise
class EmbeddedVideo(BodyTextCheck):

    # Title for the check
    title = "HTML: Embedded Video"

    # Description for the check
    description = "Videos (e.g. YouTube videos) should be created as 'Videos' in an article, rather than embedded in the HTML of Article Pages."

    # Action
    action = "Remove video embed code (iframe) from page, and create a 'Video' inside the article."

    # Video URLs
    video_urls = ['youtube.com', 'vimeo.com']

    def check(self):

        embeds = self.soup.findAll(['object', 'iframe', 'embed',])

        for i in embeds:
            if i.name == 'iframe':
                src = i.get('src', '')
                if any([x in src for x in self.video_urls]):
                    yield HighError(self, 'Found embedded video in body text.')

        if embeds:
            yield LowError(self, 'Found embedded content (iframe, embed, or object) in body text.')


# Prohibited words and phrases. Checks for individual words, phrases, and regex patterns in body text.
class ProhibitedWords(BodyTextCheck):

    title = "HTML: Words/phrases to avoid."

    description = "In order to follow style or editoral standards, some words (e.g. 'PSU') should not be used."

    action = "Replace the words/phrases identified with appropriate alternatives."

    # List of individual words (alphanumeric only, will be compared case-insenstive.)
    find_words = ['PSU',]

    # List of phrases, will be checked for 'in' body text.
    find_phrases = ['Cooperative Extension',]

    # Regex patterns.  These are probably 'spensive.
    find_patterns = ['https*://',]

    def check(self):

        # Get a list of individual
        words = self.words
        text = self.text.lower()

        for i in self.find_words:
            if i.lower() in words:
                yield LowError(self, 'Found word "%s" in body text.' % i)

        for i in self.find_phrases:
            if i.lower() in text:
                yield LowError(self, 'Found phrase "%s" in body text.' % i)

        for i in self.find_patterns:
            i_re = re.compile('(%s)' %i, re.I|re.M)
            _m = i_re.search(text)

            if _m:
                yield LowError(self, 'Found "%s" in body text.' % _m.group(0))


# Verifies that a lead image is assigned to the product
class HasLeadImage(ContentCheck):

    title = "Lead Image"

    description = "A quality lead image is suggested to provide a visual connection for the user, and to display in search results."

    action = "Please add a quality lead image to this product."

    @property
    def error(self):

        c = ConditionalCheck(self.context)

        # If we're a person, but not educator/faculty, no error
        if c.isPerson and not c.isEducatorFaculty:
            return NoError
        elif c.isVideo:
            return NoError

        return LowError

    # Sort order (lower is higher)
    sort_order = 5

    # Has lead image?
    @property
    def has_leadimage(self):
        return ILeadImage(self.context).has_leadimage

    @property
    def image_format(self):
        return ILeadImage(self.context).image_format

    @property
    def leadimage(self):
        if self.has_leadimage:
            return ILeadImage(self.context).get_leadimage()

    @property
    def dimensions(self):
        if self.has_leadimage:
            return ILeadImage(self.context).get_leadimage().getImageSize()

    def value(self):
        return self.has_leadimage

    def check(self):
        if not self.value():
            yield self.error(self, 'No lead image found')

# Verifies that a valid lead image format is used for the product
class LeadImageFormat(HasLeadImage):

    title = "Lead Image: Format"

    description = "Lead-images should be either JPEG (for photos) or PNG (for graphics/line art)"

    action = "Please add a quality JPEG or PNG lead image to this product."

    # Sort order (lower is higher)
    sort_order = 5

    # The image format
    def value(self):
        if self.has_leadimage:
            return self.image_format not in ('JPEG', 'PNG')

        return False

    def check(self):
        if self.value():
            yield self.error(self, 'Invalid format lead image found.')

class LeadImageOrientation(HasLeadImage):

    title = "Lead Image: Orientation"

    description = "Lead-images should be landscape orientation"

    action = "Please add a quality landscape orientation image to this product."

    @property
    def error(self):

        c = ConditionalCheck(self.context)

        # If we're a person or video, no error.  Person products are expected to
        # and videos pull the YouTube thumbnail, which is too small.
        if c.isPerson or c.isVideo:
            return NoError

        return LowError

    # Sort order (lower is higher)
    sort_order = 5

    # Check if the image width is less than the height
    def value(self):
        dimensions = self.dimensions

        if dimensions:

            (w,h) = dimensions

            return w < h

        return False


    def check(self):
        if self.value():
            yield self.error(self, 'Portrait/square orientation lead image found.')

class LeadImageWidth(LeadImageOrientation):

    minimum_image_width = 600

    title = "Lead Image: Width"

    description = "Lead-images should be at least %d pixels wide." % minimum_image_width

    action = "Please add a larger lead image to this product."

    # Check if the image width is less than the height
    def value(self):
        dimensions = self.dimensions

        if dimensions:

            (w,h) = dimensions

            return w < self.minimum_image_width

        return False

    def check(self):

        if self.value():

            (w,h) = self.dimensions

            yield self.error(self, 'Lead image width is %d pixels.' % w)

# Checks for instances of inappropriate link text in body
class AppropriateLinkText(BodyLinkCheck):

    title = 'HTML: Appropriate Link Text'

    description = "Checks for common issues with link text (e.g. using the URL as link text, 'click here', 'here', etc.)"

    action = "Linked text should be a few words that describe the content that exists at the link."

    find_words = ['click', 'http://', 'https://', 'here',]

    find_words = [x.lower() for x in find_words]

    min_chars = 5 # minimum length of link text.  Arbitrary value of 5

    def value(self):
        data = []

        for a in super(AppropriateLinkText, self).value():
            data.append(self.soup_to_text(a))

        return data

    def check(self):

        # Iterate through link text for document
        for i in self.value():

            # Minimum length check
            if len(i) < self.min_chars:
                yield LowError(self, 'Short link text "%s" ("%d" characters)' % (i, len(i)))

            # Check for individual prohibited words
            link_words = self.toWords(i)

            # Iterate through the words and check for presence in link text.
            for j in link_words:
                if j in self.find_words:
                    yield LowError(self, 'Inappropriate Link Text "%s" (found "%s")' % (i, j))

# Checks for cases where an image is linked to something
class ImageInsideLink(BodyLinkCheck):

    title = 'HTML: Image Inside Link'

    description = "Checks for <img> tags inside a link (<a> tag).  Images should not be used inside of links."

    action = "Remove link tag from around image."

    def value(self):
        images = []

        for a in super(ImageInsideLink, self).value():
            images.extend(a.findAll('img'))

        return len(images)

    def check(self):
        found_images = self.value()

        if found_images:
            yield LowError(self, 'Found %d images inside of links.' % found_images)


# Checks for cases where an image is linked to something
class ExternalAbsoluteImage(BodyImageCheck):

    title = 'HTML: Image with an external or absolute URL'

    description = "Checks for <img> tags that reference images outside the site, or use a URL path rather than Plone's internal method."

    action = "Use the rich text editor to select an image rather than the HTML source code."

    def check(self):
        for img in self.value():
            src = img.get('src', '')
            if not src.startswith('resolveuid'):
                yield LowError(self, 'Image source of "%s" references an external/absolute image.' % src)


# Checks for cases where an image is linked to something
class ResizedImage(BodyImageCheck):

    title = 'HTML: Image is resized using the rich text editor.'

    description = "Checks for <img> tags that use Plone's resizing.  All images should be full size."

    action = "Select the 'Original' size for this image in the rich text editor."

    def check(self):
        for img in self.value():
            src = img.get('src', '')
            if src.startswith('resolveuid') and '/@@images/' in src:
                yield LowError(self, 'Image "%s" uses Plone\'s resizing' % src)


# Checks for cases where an image is inside a paragraph that has text, but does not have a discreet tag.
class ImageInsideTextParagraph(BodyImageCheck):

    title = "HTML: Image inside a paragraph"

    description = "Checks for <img> tags mixed in with paragraphs of text."

    action = "Use the rich text editor to separate the image into a standalone paragraph of class 'discreet' containing only the image caption."

    # Other acceptable tags for an image to be under, in addition to the
    # standard '<p>'
    ok_parent_tags = ['td', 'li']

    def check(self):
        # Iterate through all images in HTML
        for img in self.value():

            # Find the image's parent paragraph
            p = img.findParent('p')

            if p:
                p_class = p.get('class', '').strip()
                p_text = self.soup_to_text(p)

                if p_text:

                    p_text = truncate_text(p_text, 32)

                    if p_class and p_class == 'discreet':

                        if not p.find('br'):
                            yield LowError(self, 'Image and caption "%s" needs a <br /> between image and text.' % p_text)
                    else:
                        yield LowError(self, 'Paragraph with image and text "%s" should be of class "discreet" and contain only the caption.' % p_text)

            else:

                # Check if an image is inside one of the other acceptable tags.
                # If it is, do not return an error.

                ok_parent = img.findParent(self.ok_parent_tags)

                if not ok_parent:
                    yield LowError(self, 'Image is not inside a <p> tag.')


# Checks for cases where a heading has a 'strong' or 'b' tag inside
class BoldHeadings(BodyHeadingCheck):

    title = 'HTML: Bold text inside headings.'

    description = "Headings should not contain bold text."

    action = "Remove bold text from headings"

    def check(self):
        for h in self.value():
            if h.findAll(['strong', 'b']):
                yield LowError(self, 'Heading %s "%s" contains bold text' % (h.name, self.soup_to_text(h)))


# Checks for cases where a heading has a 'strong' or 'b' tag inside
class HeadingsInBold(BoldHeadings):

    title = 'HTML: Headings inside bold text.'

    description = "Headings should not be inside bold text."

    action = "Remove bold text from around headings"

    def value(self):
        return self.soup.findAll(['strong', 'b'])

    def check(self):
        for b in self.value():
            for h in b.findAll(self.all_heading_tags):
                yield LowError(self, 'Heading %s "%s" inside bold text' % (h.name, self.soup_to_text(h)))

# Generic Image check that returns all <img> tags as the value()
class InternalLinkCheck(BodyLinkCheck):

    title = 'Internal Links'

    description = "Checks for links with no domain, or links to an extension.psu.edu URL"

    action = "Link internally using the text editor functionality. Do not link to internal content by URL."

    bad_domains = [
        'extension.psu.edu',
        'cms.extension.psu.edu',
        'sites.extension.psu.edu',
        'www.extension.psu.edu',
        'pubs.cas.psu.edu',
    ]

    ok_urls = [
        ('extension.psu.edu', '/aboutme'),
        ('extension.psu.edu', '/county-offices'),
        ('extension.psu.edu', '/counties'),
        ('extension.psu.edu', '/pa-pipe'),
        ('extension.psu.edu', '/programs'),
        ('extension.psu.edu', '/courses'),
        ('extension.psu.edu', '/associations'),
        ('extension.psu.edu', '/master-gardener'),
        ('extension.psu.edu', '/fsma'),
        ('extension.psu.edu', '/watershed-stewards'),
        ('extension.psu.edu', '/spotted-lanternfly'),
    ]

    def check(self):
        for a in self.value():
            href = a.get('href', '')

            if href:

                if self.is_bad_url(href):

                    url_text = self.soup_to_text(a)

                    yield LowError(self,
                        'Link URL "%s" (%s) links to the CMS or Extension site domain.' % (url_text, href))


# Checks for multiple sequential breaks inside a paragraph
class ParagraphMultipleBreakSequenceCheck(BodyTextCheck):

    title = 'HTML: Multiple sequential breaks inside a paragraph.'

    description = "Paragraphs should be contained in individual <p> tags, not separated by 'double breaks.'"

    action = "Replace '<br /><br />' with '</p><p>' in rich text editor."

    def check(self):

        # Iterate through all paragraphs in HTML
        for p in self.soup.findAll('p'):

            # This flag is used to break out of loops early.  It is set if a
            # double break is detected inside a paragraph.  Once we find one,
            # stop checking that paragraph.
            p_has_error = False

            # Iterate through all of the <br /> in the <p>
            for br in p.findAll('br'):

                # Stop looking if we found an error already
                if p_has_error:
                    break

                # Check the next siblings of the <br /> to see if we can find
                # another <br />, skipping whitespace.
                for next_sibling in br.nextSiblingGenerator():

                    # If next sibling is a tag, and the name is 'br', raise an error
                    if isinstance(next_sibling, Tag) and next_sibling.name == 'br':
                        p_text = truncate_text(self.soup_to_text(p), 32)
                        p_has_error = True
                        yield LowError(self, 'Double breaks found in paragraph beginning with "%s"' % p_text)
                        break
                    # If next sibling is a string, and it is whitespace, keep looking
                    elif isinstance(next_sibling, NavigableString) and not next_sibling.strip():
                        continue
                    # If it's something else, stop looking
                    else:
                        break


# Validates that file(s) inside the product aren't used elsewhere
class DuplicateFileChecksum(ContentCheck):

    title = "File Uniqueness"
    description = "Duplicate files should be avoided."
    action = "Attempt to resolve duplicate files."

    render = True
    sort_order = 6

    def html_list(self, brains):
        li = " ".join(['<li><a href="%s/view">%s</a></li>' % (x.getURL(), x.Title) for x in brains])
        ul = "<ul>%s</ul>" % li
        return ul

    def value(self):

        # Get all items inside this product
        path = '/'.join(self.context.getPhysicalPath())
        results = self.portal_catalog.searchResults({'path' : path})

        # Create a dict of { UID : r }
        return dict([(x.UID, x) for x in results if x.cksum])

    def check(self):

        # Get a dict of { UID : r } for everything in this product that has a
        # cksum indexed
        uid_cksum = self.value()

        # If we have data, look for duplicates
        if uid_cksum.values:

            # grab the individual checksums and uids for items inside this product.
            cksums = [x.cksum for x in uid_cksum.values()]
            uids = uid_cksum.keys()

            # Check for duplicate files within this product
            product_duplicate_cksums = [x for x in set(cksums) if cksums.count(x) > 1]

            if product_duplicate_cksums:
                product_brains = [x for x in uid_cksum.values()
                                  if x.cksum in product_duplicate_cksums]

                ul = self.html_list(product_brains)

                yield LowError(self, 'Duplicate files found inside this product: %s' % ul)

            # Find all items with those checksums
            duplicates = self.portal_catalog.searchResults({'cksum' : cksums})

            # Filter out UIDs inside this product
            duplicates = [x for x in duplicates if x.UID not in uids]

            # If we found duplicate files outside this product
            if duplicates:
                ul = self.html_list(duplicates)
                yield LowError(self, 'Duplicate files found in other products: %s' % ul)

# Check for URL shortener links in body text
class URLShortenerCheck(BodyLinkCheck):

    title = "HTML: URL Shortener"
    description = "URLs from url shorteners (bit.ly, tinyurl.com, goo.gl) should not be used in the product text."
    action = "Use the full URL of the content for this link."

    bad_domains = ['bit.ly', 'tinyurl.com', 'goo.gl', 'youtu.be', 't.co', 'ow.ly', 'psu.ag']

    ok_urls = [
        ('goo.gl', '/maps'), # Google Maps short URL is fine
    ]

    def check(self):

        for a in self.value():
            href = a.get('href', '')

            if self.is_bad_url(href):
                yield LowError(self, 'Short URL "%s" found for link "%s"' % (href, self.soup_to_text(a)))

# Checks ALL CAPS headings
class AllCapsHeadings(BodyHeadingCheck):

    title = 'HTML: Headings in ALL CAPS.'

    description = "Headings should not use ALL CAPS text."

    action = "Make headings title case."

    def check(self):
        for h in self.value():
            h_text = self.soup_to_text(h)

            # Skip headings that are one-word headings.  They're sometimes acronyms.
            if len(self.toWords(h_text)) > 1:

                if h_text == h_text.upper():
                    yield LowError(self, '%s heading "%s" has ALL CAPS.' % (h.name, h_text))

# Checks for presence of <u> tag in body text.
class UnderlinedText(BodyTextCheck):

    title = "HTML: Underlined Text"

    description = "Text should not be underlined."

    action = "Remove <u> tag(s) from HTML."

    def check(self):
        for u in self.soup.findAll('u'):
            text = self.soup_to_text(u)
            yield LowError(self, 'Found underlined text "%s"' % text)


# Checks for presence of inline styles
class InlineStyles(BodyTextCheck):

    title = "HTML: Inline styles"

    description = "Inline styles should not be used."

    action = "Remove inline styles from HTML."

    def check(self):
        for i in self.soup.findAll():
            style = i.get('style', '')
            if style:
                i_text = self.soup_to_text(i)
                yield LowError(self, 'Inline style "%s" found for %s "%s"' % (style, i.name, i_text)   )

# Checks for presence of inline styles
class ProhibitedAttributes(BodyTextCheck):

    # These attributes are prohibited, except for the values specified.
    attribute_config = {
        'width' : None,
        'height' : None,
        'align' : {
            'p' : ['left'],
            'td' : ['left', 'right', 'center'],
            'th' : ['left', ],
        }
    }

    title = "HTML: Prohibited Attributes"

    description = "Some HTML attributes should not be used."

    action = "Remove these attributes from the HTML."

    def check(self):

        _re = re.compile('\S+')

        for (_attr, ok_values) in self.attribute_config.iteritems():

            for i in self.soup.findAll(attrs={_attr : _re}):

                is_ok = False

                _attr_value = i.get(_attr, None)

                # Null values are fine
                if _attr_value is None:
                    is_ok = True

                # If we're a string
                elif isinstance(_attr_value, (unicode, str)):

                    # Remove whitespace
                    _attr_value = _attr_value.strip()

                    # Empty values are fine
                    if not _attr_value:
                        is_ok = True

                    # If we have an "OK Value" configured, and our value is in
                    # that list, we're fine
                    if ok_values:
                        is_ok = _attr_value in ok_values.get(i.name, [])

                if not is_ok:

                    yield LowError(self,
                            u'Prohibited attribute (<%s %s="%s" ... />) found.' % (
                            i.name,
                            _attr,
                            _attr_value,
                        )
                    )


# Validate that resolveuid/... links actually resolve, and that they link to a product or a file.
class InternalLinkByUID(BodyLinkCheck):

    title = 'HTML: Internal Links By Plone Id'

    description = "Validation for links using the Plone id rather than a URL."

    action = "Update link to point to a valid and active product, or a file/image inside this product."

    def value(self):
        return self.soup.findAll(['a', 'img'])

    @property
    def internal_links(self):

        # Checks for the 'resolveuid' string in the raw HTML
        if 'resolveuid' in self.html:

            # Iterates through the link tags, and grabs the href value
            for a in self.value():

                href = None
                link_type = None

                if a.name in ['a']:
                    href = a.get('href', '')
                    link_type = "Link"
                elif a.name in ['img']:
                    href = a.get('src', '')
                    link_type = "Image"

                # If we found an href...
                if href:

                    # Check for a regex match
                    m = self.resolveuid_re.search(href)

                    if m:
                        # Grab the contents of the href to use in an error message
                        href_text = self.soup_to_text(a)

                        # Pull the UID from the href
                        linked_uid = m.group(1)

                        # Grab the catalog brain by the UID
                        linked_brain = self.uid_to_brain.get(linked_uid, None)

                        # If we found a brain, get the linked object
                        if linked_brain:
                            linked_object = linked_brain.getObject()
                        else:
                            linked_object = None

                        _ = self.object_factory(
                            href=href,
                            text=href_text,
                            uid=linked_uid,
                            brain=linked_brain,
                            object=linked_object,
                            link_type=link_type,
                        )

                        yield(_)

    def check(self):

        # Loop through the links
        for link in self.internal_links:

            # If we found a brain, run some checks
            if link.brain:

                # If it is a file or image, verify that it lives inside this
                # product.
                if link.brain.Type in ['File', 'Image']:

                    linked_object_parent_uid = link.object.aq_parent.UID()
                    product_uid = None

                    for o in aq_chain(self.context):

                        if IAtlasProduct.providedBy(o):
                            product_uid = o.UID()
                            break

                        elif IPloneSiteRoot.providedBy(o):
                            break

                    if product_uid != linked_object_parent_uid:
                        yield MediumError(self,
                            '%s "%s" references a %s outside this product.' % (link.link_type, link.text, link.brain.Type))

                # If it's not a file, verify that it's a product.
                else:

                    # If the linked object is a product, verify that
                    # its workflow is an active state
                    if IAtlasProduct.providedBy(link.object):

                        review_state = link.brain.review_state

                        if review_state not in ACTIVE_REVIEW_STATES:
                            yield MediumError(self,
                                '%s "%s" links to an inactive product.' % (link.link_type, link.text))

                    # Return an error if it's not a product
                    else:
                        yield MediumError(self,
                            '%s "%s" must link to a product/file/image, not a(n) "%s".' % (link.link_type, link.text, link.brain.Type))

            # Return an error if we can't find the brain
            else:
                yield MediumError(self,
                    '%s "%s" does not resolve to a valid object.' % (link.link_type, link.text))

# Validates that an event is inside a group product
class EventGroupParent(ContentCheck):

    title = "Parent Group Product"

    @property
    def description(self):
        return u"%s products must be inside a Group Product" % self.context.Type()

    action = "Move this product into an appropriate group product."

    parent_schema = IEventGroup

    # Sort order (lower is higher)
    sort_order = 2

    def value(self):
        return self.context.aq_parent

    def check(self):
        v = self.value()

        if not self.parent_schema.providedBy(v):
            yield MediumError(self, u"Product has %s as a parent." % v.Type())

# Flags workshops that have not had an event in the past year
class WorkshopGroupUpcomingWorkshop(ContentCheck):

    title = "Upcoming Workshop"

    description = "Checks for Workshop Groups that have not had a Workshop in the past year."

    action = "Review and potentially expire this product."

    limit = 365

    # Sort order (lower is higher)
    sort_order = 3

    # End dates for events
    def value(self):
        _ = EventGroupDataAdapter(self.context).getPages()
        return sorted([x.end for x in _])

    def check(self):
        v = self.value()

        if v:
            most_recent_workshop = max(v)
            date_diff = self.now - most_recent_workshop
            if date_diff.days > self.limit:
                yield LowError(self, u"The most recent Workshop for this Workshop Group was %d days ago." % date_diff.days)
        else:
            yield LowError(self, u"This Workshop Group has no Workshops.")

# Flags webinar groups that have no upcoming webinars and no recordings
class WebinarGroupWebinars(ContentCheck):

    title = "Upcoming Webinars or Recordings"

    description = "Checks for Webinar Groups have no upcoming webinars and no recordings"

    action = "Review and potentially expire this product."

    # Sort order (lower is higher)
    sort_order = 3

    @property
    def upcoming_events(self):

        _ = EventGroupDataAdapter(self.context).getPages()

        now = self.now

        return [x for x in _ if x.end > now]

    @property
    def webinar_recordings(self):
        _ = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.event.webinar.recording.IWebinarRecording',
            'path' : "/".join(self.context.getPhysicalPath()),
        })

        return [x.getObject() for x in _]

    def value(self):
        return self.upcoming_events + self.webinar_recordings

    def check(self):

        if not self.value():
            yield LowError(self, u"This Webinar Group has no upcoming webinars and no recordings")

# Validates that the video is in the Penn State Extension channel
class ExtensionVideoChannel(ContentCheck):

    title = "YouTube Video Channel"

    description = "Validates that the video is in the Penn State Extension channel"

    action = "Move video to the Penn State Extension channel and update the URL in the product."

    valid_channels = [
        'UCJBLYNMZSQQrotFPzrv6I7A', # Extension
        'UCKNxhWl61jLdxmxjNFntVzA', # College
    ]

    def value(self):
        return getattr(self.context, 'video_channel_id', None)

    def check(self):
        v = self.value()

        if v:
            if v not in self.valid_channels:
                yield LowError(self, u"This %s is not in the Penn State Extension YouTube channel." % self.context.Type())


# Check for large images (dimensions, size)
class LargeImages(ContentCheck):

    title = "Large Images"

    description = "Validates that images contained in product are an appropriate size for the web."

    action = "Resize image to a maximum of 1200px width."

    max_width = 1500

    max_size_kb = 2048  # 2MB

    render = True

    def value(self):

        path = '/'.join(self.context.getPhysicalPath())

        v = self.portal_catalog.searchResults({'Type' : 'Image', 'path' : path})

        return [x.getObject() for x in v]

    def dimensions(self, image):
        try:
            return image.image.getImageSize()
        except:
            return (0,0)

    def size(self, image):
        try:
            return image.image.size/1024.0 # KB
        except:
            return 0

    def check(self):
        for v in self.value():

            (w,h) = self.dimensions(v)

            size = self.size(v)

            if w > self.max_width or size > self.max_size_kb:
                yield LowError(self, u"<a href=\"%s/view\">%s</a> has a width of %dpx, and is %dKB" % (v.absolute_url(), v.title, w, size))

# Parent class for Autogenerated Article Checks
class AutogeneratedArticleCheck(BodyTextCheck):

    @property
    def pdf_autogenerate(self):
        return not not getattr(self.context, 'pdf_autogenerate', False)

# Validate that Articles with the PDF autogeneration enabled do not contain files.
class AutogeneratedArticleContainingFiles(AutogeneratedArticleCheck):

    title = "Article containing files has autogenerated PDF enabled"

    description = "Articles that have autogenerated PDF enabled do not support files."

    action = "Disable the PDF autogeneration or remove files."

    render = True

    def value(self):
        return self.context.listFolderContents({'Type' : 'File'})

    def check(self):

        if self.pdf_autogenerate:

            for v in self.value():
                yield MediumError(self, u"%s contains %s <a href=\"%s/view\">%s</a>." % (
                    self.context.Type(),
                    v.Type(),
                    v.absolute_url(),
                    v.title
                ))

# Validate that Articles with the PDF autogeneration enabled do not contain
# internal links in HTML text.
class AutogeneratedArticleInternalLinks(AutogeneratedArticleCheck):

    title = "Article containing internal links has autogenerated PDF enabled"

    description = "Articles that have autogenerated PDF enabled do not support internal links."

    action = "Disable the PDF autogeneration or remove internal links."

    render = True

    def value(self):
        return [x for x in self.soup.findAll('a') if self.resolveuid_re.match(x.get('href', ''))]

    def check(self):

        if self.pdf_autogenerate:

            for v in self.value():
                yield MediumError(self, u"%s contains internal link %r." % (
                    self.context.Type(),
                    v
                ))

# Validate that active people have valid classification(s)
class ActivePersonClassifications(ConditionalCheck):

    title = "Person Classifications"

    description = "Validates that people in an Active state are assigned classifications."

    action = "Assign Classifications (e.g. Educator, Faculty, Staff, etc.) to this person."

    def value(self):
        return self.classifications

    def check(self):
        if self.review_state in ['published',] and not self.value():
            yield MediumError(self, u"%s %s has no Classifications." % (
                self.context.Type(),
                self.context.Title()
            ))


# Validate that active people have one and only one location
class ActivePersonCountyLocation(ContentCheck):

    title = "Person County/Location"

    description = "Validates that people in an Active state have one and only one County/Location assigned."

    action = "Assign a single 'County/Location' to this person under the 'Professional Information' tab."

    def value(self):

        county = getattr(self.context, 'county', [])

        if not county:
            county = []

        return len(county)


    def check(self):
        if self.review_state in ['published',]:
            v = self.value()

            if v < 1:
                yield LowError(self, u"%s %s has no County/Location value." % (
                    self.context.Type(),
                    self.context.Title()
                ))
            elif v > 1:
                yield LowError(self, u"%s %s has %d County/Location values." % (
                    self.context.Type(),
                    self.context.Title(),
                    self.value()
                ))

# Validate that Magento URLs for products are either a normalized version of the
# title, or match the short URL of the Plone product (as a way to say, "This is OK")

class MagentoURLCheck(ConditionalCheck):

    # Title for the check
    title = "Magento URL Key"

    # Description for the check
    description = "Validate that Magento URLs for products are meaningful."

    # Action to remediate the issue
    action = "Fix the URL in Magento, or if the Magento URL is correct, set the short name of the product in Plone."

    # Sort order (lower is higher)
    sort_order = 20

    @property
    def error(self):

        # Check if we're a person.  Not checking URLs for people.
        if self.isPerson:
            return NoError

        return LowError

    def value(self):
        return getattr(self.context, 'magento_url', None)

    def check(self):

        # Don't check URLs for internal-only products
        # Child products do not require sane URLs
        if self.isExternalStore and not self.isChildProduct:

            magento_url = self.value()

            if magento_url:

                valid_url_keys = [ploneify(self.context.title), self.context.getId()]

                if magento_url not in valid_url_keys:
                    yield self.error(self, u"Magento URL Key '%s' may need to be fixed." % magento_url)

# Validates that event groups (Workshop, Webinar, Course, Conference) have
# at least minimal body text
class EventGroupBodyText(BodyTextCheck):

    # Title for the check
    title = "Product Long Description"

    # Description for the check
    description = "Validate that this product has body text."

    # Action to remediate the issue
    action = "Add information to the 'Text' field for this product."

    # Minimum Length
    minimum_length = 25

    def value(self):
        return self.text

    def check(self):

        if not self.value() or len(self.value()) < self.minimum_length:
            yield MediumError(self, u"Product Long Description is less than %d characters." % self.minimum_length)

# Check for external links.  It doesn't make sense to check external
# links on every save, but this will allow us to do it on-demand if they exist.
class ExternalLinkCheck(InternalLinkCheck):

    # Title for the check
    title = "External Links"

    # Description for the check
    description = "Checks for the presence of external links, and provides a link to run a manual check."

    # Action to remediate the issue
    @property
    def action(self):
        return "<a href=\"%s/@@link_check\">Run an external link check.</a>" % self.context.absolute_url()

    # Timeout
    timeout = 20

    # Render message as HTML
    render = True

    # Render action as HTML
    render_action = True

    # Link Check
    redis_cachekey = "LINK_CHECK"

    @property
    def whitelisted_urls(self):
        return self.registry.get('agsci.atlas.link_check.whitelist', [])

    def getExternalLinks(self):

        for a in self.getLinks():

            href = a.get('href', '')

            if href:

                (scheme, domain, path) = self.parse_url(href)

                if scheme in ('http', 'https') and domain not in self.bad_domains:
                    yield (href, a.text)

    def value(self):
        return list(set(self.getExternalLinks()))

    # Construct a cache key
    def url_cache_key(self, url):
        return "|".join([self.redis_cachekey, url])

    # Given a URL grab the link check results from the cache
    def get_cached_data(self, url):

        data = self.redis.get(self.url_cache_key(url))

        if data and isinstance(data, (str, unicode)):
            return pickle.loads(data)

    # Given a URL and the link check results, cache that
    def set_cached_data(self, url, data):

        # Set timeout
        timeout = timedelta(seconds=self.CACHED_DATA_TIMEOUT)

        # Store data in redis
        self.redis.setex(self.url_cache_key(url), timeout, pickle.dumps(data))

    # Given a URL, check the whitelist, then the cache, then actualy check it
    def check_link(self, url):

        # Check for whitelist
        if url in self.whitelisted_urls:
            return (200, url)

        # See if we have it cacheck
        data = self.get_cached_data(url)

        if data:
            return data

        # If not, cache it and return it.
        data = self._check_link(url)

        self.set_cached_data(url, data)

        return data

    # Performs the "real" URL check
    def _check_link(self, url, head=False):

        # Set Firefox UA
        headers = requests.utils.default_headers()
        headers['User-Agent'] = u"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:61.0) Gecko/20100101 Firefox/61.0"

        try:

            if head:
                data = requests.head(url, timeout=30, headers=headers)

            else:
                data = requests.get(url, timeout=30, headers=headers)

        except requests.exceptions.HTTPError:
            return (404, url)

        except:
            return (999, url)

        else:

            return_code = data.status_code
            return_url = data.url

            if return_code == 200:

                if self.url_equivalent(url, return_url):
                    return(200, url)
                else:
                    return(302, return_url)

            else:

                if return_code in [301,302]:
                    return(302, return_url)

                else:
                    return (return_code, return_url)

    def check(self):

        if self.value():
            yield ManualCheckError(self,
                u"""Product contains external links."""
            )

    def manual_check(self):

        for (url, link_text) in self.value():

            (return_code, return_url) = self.check_link(url)

            data = self.object_factory(
                title=link_text,
                url=url,
                status=return_code,
                redirect_url=return_url,
            )

            if return_code in (200,):

                yield NoError(self,
                    u"""<a href=\"%s\">%s</a> is a valid link.""" %
                    (url, link_text), data=data,
                )

            elif return_code in (301, 302,):
                yield LowError(self,
                    u"""<a href=\"%s\">%s</a> is a <strong>redirect</strong> to <a href=\"%s\">%s</a>""" %
                    (url, link_text, return_url, return_url), data=data,
                )

            elif isinstance(return_code, int) and return_code > 500:
                yield HighError(self,
                    u"""<a href=\"%s\">%s</a> had a return code of <strong>%d</strong>.""" %
                    (url, link_text, return_code), data=data,
                )

            else:

                yield MediumError(self,
                    u"""<a href=\"%s\">%s</a> had a return code of <strong>%d</strong>.""" %
                    (url, link_text, return_code), data=data,
                )

# Verifies that the Plone product URL path length is within limits
class ProductURLPathLength(ContentCheck):

    # Limit of characters
    limit = 200

    # Title for the check
    title = "Product URL Path Length"

    # Description for the check
    description = "Validates that the URL path for the product is <= %d characters" % limit

    # Action to remediate the issue
    action = "Adjust the short name of the product in Plone."

    def value(self):
        site = getSite()
        site_url = site.absolute_url()
        context_url = self.context.absolute_url()
        return context_url[len(site_url):]

    def check(self):
        context_url = self.value()
        _ = len(context_url)

        if _ > self.limit:
            yield LowError(self, u"Product URL Path '%s' is %d characters." % (context_url, _))

# Warn if Publishing Dates are in the future
class FuturePublishingDate(ContentCheck):

    # Title for the check
    title = "Future Publishing Date"

    # Description for the check
    description = "Validates that the publishing date for the product is not in the future, which will prevent the product from being imported. This is occasionally the desired behavior, but is often set in error."

    # Action to remediate the issue
    action = "Adjust or remove the publishing date (under the Dates tab) of the product in Plone if it is not set for a reason."

    def value(self):
        return localize(self.context.effective())

    def check(self):
        _ = self.value()

        if _ and _ > self.now:
            yield LowError(self, u"Publishing Date %s is in the future." % _.strftime('%Y-%m-%d'))

# Checks if an article has a publication price/sku but 'available for purchase' isn't checked
class ArticlePurchase(ContentCheck):

    # Title for the check
    title = "Article Purchase Fields"

    # Description for the check
    description = "Validates that articles which has a publication SKU/price assigned also has the \"Article available for purchase?\" field checked."

    # Action to remediate the issue
    action = "If this article is available for purchase, check the \"Article available for purchase?\" field."

    def value(self):

        fields = [
            'article_purchase',
            'publication_reference_number',
            'price',
        ]

        values = [getattr(self.context, x, None) for x in fields]

        return dict(zip(fields, values))

    def check(self):
        _ = self.value()

        if (_['price'] or _['publication_reference_number']) and not _['article_purchase']:
            yield LowError(self, u"%s has a Price or Publication SKU assigned, but is not set as available for purchase." % self.context.Type())


class AlternateLanguage(BodyTextCheck):

    # Title for the check
    title = "Alternate Language Configuration"

    # Description for the check
    description = "Validates that the alternate language points to a valid SKU for that language, and that the product with that SKU has this product configured, and that this product doesn't link to the other product in the body text."

    # Action to remediate the issue
    action = "Update the Alternate Language settings as needed."

    def get_alternate_languages(self, o):
        _ = getattr(o, 'atlas_alternate_language', [])

        if _:
            return _

        return []

    def value(self):
        return self.get_alternate_languages(self.context)

    def validate_sku(self, sku=None, language=None):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'atlas_language' : language,
            'SKU' : sku,
            'review_state' : ACTIVE_REVIEW_STATES,
        })

        return [x for x in results if not x.IsChildProduct]

    def check(self):

        internal_link_uids = self.internal_link_uids

        # Get the SKU, language(s), and alternate language config assigned to
        # this product
        my_sku = getattr(self.context, 'sku', None)
        my_language = getattr(self.context, 'atlas_language', [])

        if not my_language:
            my_language = []

        alternate_language_config = self.value()

        # Check for multiple SKUs for a language
        alternate_languages = [x.get('language', None) for x in alternate_language_config]
        duplicate_languages = [x for x in set(alternate_languages) if alternate_languages.count(x) > 1]

        if duplicate_languages:
            yield LowError(self, u"Multiple SKUs configured for langage %s" % ";".join(duplicate_languages))

        # Iterate through the alternate languages
        for _ in alternate_language_config:

            # Get the SKU and language for each alternate language
            sku = _.get('sku', None)
            language = _.get('language', None)

            # Grab products that match that config
            results = self.validate_sku(sku=sku, language=language)

            # If no products match the SKU and language for the configured alternate
            # language, throw an error
            if not results:
                yield LowError(self, u"SKU %s is configured for the %s language, and is not a valid product." % (sku, language))

            # Iterate through the found products and verify that *this* product
            # is configured as an alternate language for *that* product.
            for r in results:

                # Verify that we don't link to this product in the body text
                if r.UID in internal_link_uids:
                    yield LowError(self, u"Found links in the body text to a product configured as an alternate language.")

                o = r.getObject()
                languages = self.get_alternate_languages(o)

                matching_languages = [x for x in languages if x.get('sku', None) == my_sku and x.get('language', None) in my_language]

                if not matching_languages:
                    yield LowError(self, u"SKU %s is configured as the %s language version of this product, but it does not have this product listed as an alternate language." % (sku, language))


# Checks for a missing map URL for events
class ValidateMapURL(ContentCheck):

    # Title for the check
    title = "Missing 'Map To Location' for Events"

    # Description for the check
    description = "Validates that the address is precise enough to provide a Google Maps URL, or a URL is manually configured."

    # Action to remediate the issue
    action = "Update the address fields on the Location tab to be more precise, or provide a URL in the 'Map To Location' field."

    def value(self):
        return ILocationMarker(self.context).map_url

    @property
    def needs_map(self):

        # This check is only needed for events
        if IEvent.providedBy(self.context):

            # Special case: All Cvent events implement the Location fields, but
            # Cvent events with a type of Webinar do not need to be checked.
            if ICventEvent.providedBy(self.context):
                atlas_event_type = getattr(self.context, 'atlas_event_type', None)

                if atlas_event_type in ['Webinar',]:
                    return False

            return True

    def check(self):

        # Only check for events
        if self.needs_map:

            # If we don't have a map URL, return an error.
            if not self.value():
                yield LowError(self, u"No Map To Location could be determined.")

# Verifies that publications are included in the Internal store.
class PublicationInternalStore(ContentCheck):

    # Title for the check
    title = "Publication Internal Store"

    # Description for the check
    description = "Validates that Publication product is included in the Internal store"

    # Action to remediate the issue
    action = "All publications should have the Internal store selected in the 'Store View' field under the 'Internal' tab."

    def value(self):

        _ = getattr(self.context, 'store_view_id', [])

        if not isinstance(_, (tuple, list)):
            return []

        return _

    def check(self):

        if 3 not in self.value():
            yield LowError(self, u"This %s is not configured for the Internal Store." % self.context.Type())


class UnreferencedFileOrImage(BodyTextCheck):

    types = ['Image', 'File']

    # Title for the check
    title = "Unreferenced File or Image inside product"

    # Description for the check
    description = "Validates that the product HTML references all files or images contained in the product."

    # Action to remediate the issue
    action = "Either reference the files/images noted, or remove them from the product."

    render = True

    def value(self):
        return self.context.listFolderContents({'Type' : self.types})

    def check(self):

        items = self.value()

        if items:

            internal_link_uids = self.internal_link_uids
            internal_image_uids = self.internal_image_uids

            internal_uids = internal_link_uids + internal_image_uids

            for o in items:
                _uid = o.UID()
                _type = o.Type()
                _title = o.Title()
                _url = o.absolute_url()

                data = self.object_factory(
                    type=_type,
                    title=_title,
                    url=_url,
                    uid=_uid,
                    getId=o.getId(),
                )

                href = u"""<a href="%s/view">%s: %s</a>""" % (_url, _type, safe_unicode(_title))

                if _uid not in internal_uids:
                    yield LowError(self, u"%s is not referenced in this product." % href, data=data)

                elif _type in ('File',) and _uid in internal_image_uids:
                    yield LowError(self, u"%s is used as an image rather than linked to." % href, data=data)

                elif _type in ('Image',) and _uid in internal_link_uids:
                    yield LowError(self, u"%s is linked to rather than used as an image." % href, data=data)

class UnreferencedImage(UnreferencedFileOrImage):

    types = ['Image',]

class VideoSeries(ContentCheck):

    # Title for the check
    title = "Video Series Configuration"

    # Description for the check
    description = "Validates that the SKUs for the videos listed in a series point to a valid SKU."

    # Action to remediate the issue
    action = "Update the Video Series settings as needed."

    def value(self):
        _ = getattr(self.context, 'videos', [])

        if _:
            return _

        return []

    def validate_sku(self, sku=None):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.video.IVideo',
            'SKU' : sku,
            'review_state' : ACTIVE_REVIEW_STATES,
        })

        return [x for x in results if not x.IsChildProduct]

    def check(self):

        # Iterate through the videos and validate the SKU
        for _ in self.value():

            # Get the SKU for each video
            sku = _.get('sku', None)

            # Ensure there *is* a SKU
            if not sku:
                yield MediumError(self, u"No SKU provided for video")
            else:

                # Grab products that match that config
                results = self.validate_sku(sku=sku)

                # If no products match the SKU for the configured video, throw an error
                if not results:
                    yield MediumError(self, u"SKU %s is configured as a video in this series and is not a valid product." % (sku, ))