from BeautifulSoup import BeautifulSoup
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from functools import wraps
from zope.annotation.interfaces import IAnnotations
from zope.component import subscribers
from zope.globalrequest import getRequest
from zope.interface import Interface

from agsci.leadimage.interfaces import ILeadImageMarker as ILeadImage
from .error import HighError, MediumError, LowError
from ..vocabulary.calculator import AtlasMetadataCalculator

import re

alphanumeric_re = re.compile("[^A-Za-z0-9]+", re.I|re.M)

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
    levels = ['High', 'Medium', 'Low']

    for i in subscribers((context,), IContentCheck):
        try:
            for j in i:
                errors.append(j)
        except Exception as e:
            errors.append(
                LowError(i, u"Internal error running check: '%s: %s'" % (e.__class__.__name__, e.message))
            )

    errors.sort(key=lambda x: levels.index(x.level))

    return errors

# This is a decorator (@context_memoize) that memoizes no-parameter methods based
# on the method name and UID for the context. The purpose is to not have to call
# ".html", ".text", ".soup", etc. many times for many different checks.
#
# Rudimentary tracking shows a 30% increase in performance, which will be more
# apparent as we're running more checks.
def context_memoize(func):

    @wraps(func)
    def func_wrapper(name):
        key = getKey(func, name)
        return getCachedValue(func, key, name)

    def getKey(func, name):
        uid = name.context.UID()
        method = func.__name__
        return '-'.join([method, uid])

    def getCachedValue(func, key, name):
        request = getRequest()

        cache = IAnnotations(request)

        if cache.has_key(key):
            return cache.get(key)

        cache[key] = func(name)

        return cache[key]

    return func_wrapper


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

    def __init__(self, context):
        self.context = context

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
    def portal_transforms(self):
        return getToolByName(self.context, 'portal_transforms')

    def __iter__(self):
        return self.check()

# Validates the product title length
class TitleLength(ContentCheck):

    title = "Product Title Length"
    description = "Titles should be no more than 60 characters."
    action = "Edit the title to be no more than 60 characters.  For short titles, add more detail."

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

    title = "Product Description Length"
    description = "Product must have a description, which should be a maximum of 160 characters."
    action = "Edit the description to be no more than 160 characters.  For short or missing descriptions, add more detail."

    def value(self):
        return len(self.context.description)

    def check(self):

        v = self.value()

        if v > 255:
            yield HighError(self, u"%d characters is too long." % v)
        elif v > 200:
            yield MediumError(self, u"%d characters is too long." % v)
        elif v > 160:
            yield LowError(self, u"%d characters is too long." % v)
        elif v == 0:
            yield HighError(self, u"A description is required for this product.")
        elif v < 32:
            yield LowError(self, u"%d characters may be too short." % v)


# Validates that the right number of EPAS categories are selected
# Parent class with basic logic
class ProductEPAS(ContentCheck):

    title = "EPAS Selections"
    fields = ('atlas_state_extension_team', 'atlas_program_team', 'atlas_curriculum')
    action = "Under the 'Categorization' tab, select the appropriate EPAS information"

    required_values = [
        (1,1,1),
    ]

    # Number of selections for each field.
    def value(self):
        try:
            return tuple([len(getattr(self.context, x, [])) for x in self.fields])
        except TypeError:
            return (0,0,0)

    def check(self):
        v = self.value()

        if v not in self.required_values:
            yield HighError(self, u"Selections incorrect.")


# Validates that the right number of EPAS categories are selected
class ArticleEPAS(ProductEPAS):

    description = "Articles should have one each of State Extension Team, Program Team, and Curriculum selected."


class VideoEPAS(ProductEPAS):

    description = "Videos should have one each of State Extension Team, Program Team, and Curriculum selected."


class ProductCategoryValidation(ContentCheck):

    category_fields = [1, 2]

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
            available_v2 = [x.value for x in vocabulary._terms if x.value.startswith('%s:' % i)]

            if available_v2:
                if not (set(v2) & set(available_v2)):

                    yield HighError(self, (u"Values for Category Level %d '%s' " +
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
            yield HighError(self, u"Category Level 1 must be assigned.")


# Validates that a Category Level 2 is selected for all Category Level 1's
# that are available.
class ProductCategory2(ProductCategoryValidation):

    pass


# Validates that a Category Level 3 is selected for all Category Level 2's
# that are available.
class ProductCategory3(ProductCategoryValidation):

    category_fields = [2, 3]


# Checks for issues in the text.  This doesn't actually check, but is a parent
# class for other checks.
class BodyTextCheck(ContentCheck):

    # Title for the check
    title = "Body Text Check"

    # Description for the check
    description = ""

    @property
    def contents(self):
        if hasattr(self.context, 'getPages'):
            return self.context.getPages()

        return []

    def getHTML(self, o):
        if hasattr(o, 'text') and hasattr(o.text, 'raw'):
            return o.text.raw

        return ''

    def html_to_text(self, html):
        text = self.portal_transforms.convert('html_to_text', html).getData()
        return " ".join(text.strip().split())

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

        return ' '.join(v)

    @property
    @context_memoize
    def text(self):
        return self.html_to_text(self.html)

    def toWords(self, text):
        text = alphanumeric_re.sub(' ', text.lower()).split()
        return list(set(text))

    @property
    def words(self):
        return self.toWords(self.text)

    def check(self):
        pass


# Checks for appropriate heading level hierarchy, e.g. h2 -> h3 -> h4
class HeadingLevels(BodyTextCheck):

    # Title for the check
    title = "HTML: Heading Levels"

    # Description for the check
    description = "Validates that the heading level hierarchy is correct."

    # Remedial Action
    action = "In the product text (including any pages for Articles), validate that the heading levels are in the correct order, and none are skipped."

    # h1 - h6
    all_heading_tags = ['h%d' % x for x in range(1,7)]

    # Get heading tag objects
    def getHeadingTags(self):
       return self.soup.findAll(self.all_heading_tags)

    def check(self):

        headings = self.getHeadingTags()

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
class HeadingLength(HeadingLevels):

    # Title for the check
    title = "HTML: Heading Text Length"

    # Description for the check
    description = "Validates that the heading text is not too long. "

    # Remedial Action
    action = "Ensure that headings are a maximum of 120 characters, and ideally 60 characters or less."

    def check(self):
        headings = self.getHeadingTags()

        for i in headings:
            html = repr(i)
            text = self.html_to_text(html)

            v = len(text)

            if v > 200:
                yield HighError(self, u"Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > 120:
                yield MediumError(self, u"Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > 60:
                yield LowError(self, u"Length of %d characters for <%s> heading '%s' may be too long." % (v, i.name, text))


# Verifies that the product title is unique for that type of product
class ProductUniqueTitle(ContentCheck):

    # Title for the check
    title = "Unique Product Title"

    # Description for the check
    description = "Validates that the product title is unique within a product type."

    action = "Add additional context to the title, or combine multiple related articles."

    # Render the output as HTML.
    render = True

    def value(self):

        # Remove parenthesis from actual title to avoid catalog errors.
        _title = self.context.title.replace('(', '').replace(')', '')

        # Query catalog for all objects of the same type with the same title
        results = self.portal_catalog.searchResults({'Type' : self.context.Type(),
                                                     'Title' : _title })

        # Removes the entry for this product
        results = filter(lambda x: x.UID != self.context.UID(), results)

        # Find titles that exactly match.
        results = filter(lambda x: x.Title.strip().lower() == self.context.title.strip().lower(), results)

        # Returns the rest of the matching brains
        return results

    def check(self):
        value = self.value()
        if value:
            urls = "<ul>%s</ul>" % " ".join(["<li><a href='%s'>%s</a></li>" % (x.getURL(), x.Title) for x in value])
            yield MediumError(self, u"%s(s) with a duplicate title found at: %s" % (self.context.Type(), urls))


# Verifies that the product owner is a valid person in the directory.
class ProductValidOwners(ContentCheck):

    # Title for the check
    title = "Valid Owner(s)"

    # Description for the check
    description = "Validates that the owner id(s) are active individuals in the directory"

    action = "Under the 'Ownership' tab, ensure that all of the ids listed in the 'Owners' field are active in the directory"

    def value(self):
        # Get the owners
        owners = getattr(self.context, 'owners', [])

        # Filter out blank owners
        return [x for x in owners if x]

    def validPeopleIds(self):
        # Get the current date/time
        now = DateTime()

        # Search for non-expired people
        results = self.portal_catalog.searchResults({'Type' : 'Person',
                                                     'expires' : {'range' : 'min',
                                                                  'query' : now
                                                                 }
                                                     })

        # Get the usernames
        user_ids = map(lambda x: getattr(x.getObject(), 'username', None), results)

        # Filter out empty usernames
        user_ids = [x for x in user_ids if x]

        return user_ids

    def check(self):
        # Get the owners, and the valid users
        value = set(self.value())
        user_ids = set(self.validPeopleIds())

        # Find any invalid users
        invalid_user_ids = list(value - user_ids)

        # Raise a warning if invalid users are found.
        if invalid_user_ids:
            invalid_user_ids = ", ".join(invalid_user_ids)
            yield MediumError(self, u"Product owner id(s) '%s' are invalid." % invalid_user_ids)


# Checks for embedded videos (iframe, embed, object, etc.) in the text.
# Raises a High if there's a YouTube or Vimeo video (specifically) or a
# Low otherwise
class EmbeddedVideo(BodyTextCheck):

    # Title for the check
    title = "Embedded Video"

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

    title = "Words/phrases to avoid."

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
                yield LowError(self, 'Found in "%s" in body text.' % _m.group(0))


# Verifies that a lead image is assigned to the product
class HasLeadImage(ContentCheck):

    title = "Lead Image"

    description = "A quality lead image is suggested to provide a visual connection for the user, and to display in search results."

    action = "Please add a quality lead image to this product."

    def value(self):
        return ILeadImage(self.context).has_leadimage

    def check(self):
        if not self.value():
            yield LowError(self, 'No lead image found')

# Checks for instances of inappropriate link text in body
class AppropriateLinkText(BodyTextCheck):

    title = 'Appropriate Link Text'

    description = "Checks for common issues with link text (e.g. using the URL as link text, 'click here', 'here', etc.)"

    action = "Linked text should be a few words that describe the content that exists at the link."

    find_words = ['click', 'http://', 'https://', 'here',]

    find_words = [x.lower() for x in find_words]

    def value(self):
        data = []

        for a in self.soup.findAll('a'):
            link_text = self.html_to_text(repr(a))
            data.append(link_text)

        return data

    def check(self):
        for i in self.value():
            link_words = self.toWords(i)
            data = []
            for j in link_words:
                if j in self.find_words:
                    yield LowError(self, 'Inappropriate Link Text "%s" (found "%s")' % (i, j))