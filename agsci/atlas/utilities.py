from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser
from Acquisition import aq_base
from BeautifulSoup import BeautifulSoup
from DateTime import DateTime
from PIL import Image
from Products.CMFPlone.CatalogTool import SIZE_CONST, SIZE_ORDER
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.utils import safe_unicode
from StringIO import StringIO
from datetime import datetime
from plone.app.layout.viewlets.content import ContentHistoryViewlet
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from plone.dexterity.interfaces import IDexterityFTI
from plone.i18n.normalizer import idnormalizer, filenamenormalizer
from plone.memoize.instance import memoize
from plone.namedfile.file import NamedBlobImage
from zLOG import LOG, INFO
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.component.interfaces import ComponentLookupError
from zope.interface import Interface
from zope.interface.interface import Method
from zope.globalrequest import getRequest
from zope.schema.interfaces import IVocabularyFactory

import pytz
import base64
import os
import re
import unicodedata

from .constants import CMS_DOMAIN, DEFAULT_TIMEZONE, IMAGE_FORMATS, \
                       API_IMAGE_QUALITY, API_IMAGE_WIDTH
from .content.article import IArticle
from .content.slideshow import ISlideshow
from .content.vocabulary.calculator import AtlasMetadataCalculator

from .interfaces import IArticleMarker, ISlideshowMarker

# Convert a Plone DateTime to a ISO formated string
def toISO(v):

    if isinstance(v, DateTime):
        try:
            tz = pytz.timezone(v.timezone())
        except pytz.UnknownTimeZoneError:
            # Because that's where we are.
            tz = pytz.timezone(DEFAULT_TIMEZONE)

        tmp_date = datetime(v.year(), v.month(), v.day(), v.hour(),
                            v.minute(), int(v.second()))

        if tmp_date.year not in [2499, 1000]:
            return tz.localize(tmp_date).isoformat()

    return None

# Localize all DateTime/datetime values to Eastern Time Zone
def localize(_):

    tz = pytz.timezone(DEFAULT_TIMEZONE)

    if isinstance(_, DateTime):

        try:
            tz = pytz.timezone(_.timezone())
        except pytz.UnknownTimeZoneError:
            pass

        _ = _.asdatetime()

    if isinstance(_, datetime):

        if not _.tzinfo:
            return tz.localize(_)

        return _

    return None

def encode_blob(f, show_data=True):

    data = getattr(f, 'data', None)

    if data:

        content_type = getContentType(f)

        if show_data:

            # Downsize images
            if isinstance(f, NamedBlobImage):

                # Only scale if we're jpg or png.  Some gifs are animated, so we
                # don't want to scale them.
                if content_type in ('image/jpeg', 'image/png'):

                    try:

                        scaled_data = scaleImage(
                            f,
                            max_width=API_IMAGE_WIDTH,
                            quality=API_IMAGE_QUALITY
                        )

                    except:
                        pass

                    else:

                        # Rudimentary check to ensure that we made a reduction in
                        # the size of the data
                        if scaled_data and len(scaled_data) < len(data):
                            data = scaled_data

            return (content_type, base64.b64encode(data))

        return (content_type, '')

    return (None, None)

def getContentType(i):
    for j in ['getContentType', 'contentType', 'content_type']:

        v = getattr(i, j, None)

        if v:

            if hasattr(v, '__call__'):
                return v()

            return v

    return None

def increaseHeadingLevel(text):
    if '<h2' in text:
        for i in reversed(range(1, 6)):
            from_header = "h%d" % i
            to_header = "h%d" % (i+1)
            text = text.replace("<%s" % from_header, "<%s" % to_header)
            text = text.replace("</%s" % from_header, "</%s" % to_header)
    return text

# Get HTML for Image with caption/description
def getImageHTML(uid, title=None, description=None, leadimage=False):
    html = ''

    html = u"""<img src="resolveuid/%s" /><br />""" % uid

    # Lead images have no description (just a title/caption) and that should
    # not be bolded.
    if leadimage:
        html = html + u"%s" % title
    else:
        html = html + u"<strong>%s</strong>" % title

    if description:
        html = html + u"""<br />%s""" % description

    html = u"""<p class="discreet">""" + html + "</p>"

    return html

# Returns the HTML for the body text of the object, handling the special case
# for multi-page articles needing headings.
def getBodyHTML(context):

    # Initialize value
    html = ''

    # Get parent object
    parent = context.aq_parent

    # Strip acquisition
    _context = aq_base(context)

    # First, get the HTML
    if hasattr(_context, 'text') and hasattr(_context.text, 'raw'):
        if _context.text.raw:
            html = _context.text.raw

    # Handle a slideshow by addin ga paragraph per image.
    if ISlideshow.providedBy(context):

        for img in ISlideshowMarker(context).getImages():

            title = img.Title().decode('utf-8')
            description = img.Description().decode('utf-8')
            uid = img.UID()

            _html = getImageHTML(uid, title=title, description=description)

            html = html + _html

    # If the parent is a multi-page article
    if IArticle.providedBy(parent):

        # Check if it's multi-page
        adapted_parent = IArticleMarker(parent)

        if adapted_parent.isMultiPage():

            # Check the config for the "Show title as heading" checkbox
            show_title_as_heading = getattr(_context, 'show_title_as_heading', False)

            # If that's checked, and this page is the first page, do an additional
            # check to make sure that the page title doesn't match the article title.
            #
            # Never show a heading duplicating an article title.
            if show_title_as_heading and adapted_parent.isFirstPage(_context):
                show_title_as_heading = not ploneify(parent.title) == ploneify(_context.title)

            # If we're still showing the title as a heading,
            if show_title_as_heading:
                html = increaseHeadingLevel(html)
                html = (u"<h2>%s</h2>\n" % _context.title) + html

    html = scrubHTML(html)

    return html

def scrubHTML(html):

    # Only operate on strings/unicode
    if not isinstance(html, (str, unicode)):
        return HTML

    # Get a BeautifulSoup instance
    soup = BeautifulSoup(html)

    # Remove the 'target' attribute from links.
    targets = []

    for a in soup.findAll('a'):
        target = a.get('target', '')
        if target:
            targets.append(target)

    if targets:
        _re = re.compile(u"""\s*target=\s*['"]%s['"]""" % "|".join(targets))
        html = _re.sub('', html)

    # Return updated value
    return html

def format_value(x, date_format='%Y-%m-%d'):

    def inline_list(x):

        if x:
            if isinstance(x, (list, tuple)):
                return '; '.join(sorted(x))

            elif isinstance(x, (str, unicode)):
                return x

        return ''

    if isinstance(x, (str, unicode)):
        return safe_unicode(" ".join(x.strip().split()))
    elif isinstance(x, bool):
        return {True : 'Yes', False : 'No'}.get(x, 'Unknown')
    # Updates the format to human-readable for an integer or float
    elif isinstance(x, (int, float)):
        return "{:,}".format(x)
    elif isinstance(x, (DateTime, datetime)):
        return x.strftime(date_format)
    elif isinstance(x, (list, tuple)):
        return inline_list(x)
    elif type(x) in [type(MissingValue), type(None)] :
        return ''
    else:
        return repr(x)

# Copied almost verbatim from http://docs.plone.org/develop/plone/security/permissions.html

class UnrestrictedUser(BaseUnrestrictedUser):
    """Unrestricted user that still has an id.
    """
    def getId(self):
        """Return the ID of the user.
        """
        return self.getUserName()

def execute_under_special_role(roles, function, *args, **kwargs):
    """ Execute code under special role privileges.

    Example how to call::

        execute_under_special_role(portal, "Manager",
            doSomeNormallyNotAllowedStuff,
            source_folder, target_folder)


    @param portal: Reference to ISiteRoot object whose access controls we are using

    @param function: Method to be called with special privileges

    @param roles: User roles for the security context when calling the privileged code; e.g. "Manager".

    @param args: Passed to the function

    @param kwargs: Passed to the function
    """

    portal = getSite()
    sm = getSecurityManager()

    try:
        try:
            # Clone the current user and assign a new role.
            # Note that the username (getId()) is left in exception
            # tracebacks in the error_log,
            # so it is an important thing to store.
            tmp_user = UnrestrictedUser(
                sm.getUser().getId(), '', roles, ''
                )

            # Wrap the user in the acquisition context of the portal
            tmp_user = tmp_user.__of__(portal.acl_users)
            newSecurityManager(None, tmp_user)

            # Call the function
            return function(*args, **kwargs)

        except:
            # If special exception handlers are needed, run them here
            raise
    finally:
        # Restore the old security manager
        setSecurityManager(sm)

#Ploneify
def ploneify(toPlone, filename=False):

    # Start with Unicode
    ploneString = safe_unicode(toPlone)

    # Replace specific characters that aren't caught by the unicode transform
    for (_f, _t) in [
        # Various dash-y characters
        (u'\u2010', u'-'),
        (u'\u2011', u'-'),
        (u'\u2012', u'-'),
        (u'\u2013', u'-'),
        (u'\u2014', u'-'),
        (u'\u2015', u'-'),
    ]:
        ploneString = ploneString.replace(_f, _t)

    # Convert accented characters to ASCII
    # Ref: https://stackoverflow.com/questions/14118352/how-to-convert-unicode-accented-characters-to-pure-ascii-without-accents
    ploneString = unicodedata.normalize('NFD', ploneString).encode('ascii', 'ignore')

    # Normalize using the system utility
    if filename:
        ploneString = filenamenormalizer.normalize(ploneString, max_length=99999)
        ploneString = re.sub('[-\s]+', '_', ploneString) # Replace whitespace with underscores
    else:
        ploneString = idnormalizer.normalize(ploneString, max_length=99999)

    # Remove leading/trailing dashes
    ploneString = re.sub("-$", "", ploneString)
    ploneString = re.sub("^-", "", ploneString)

    return ploneString

def truncate_text(v, max_chars=200, el='...'):

    if v and isinstance(v, (str, unicode)):

        v = " ".join(v.strip().split())

        if len(v) > max_chars:
            v = v[:max_chars]
            _d = v.split()
            _d.pop()
            v = " ".join(_d) + el

    return v


class SitePeople(object):

    # Workflow states
    active_review_state = 'published'
    inactive_review_state = 'published-inactive'

    def __init__(self, active=True):
        self.context = getSite()
        self.active = active

    def get_key(self):
        return "-".join([self.__class__.__name__, repr(self.active)])

    @property
    def request(self):
        return getRequest()

    @property
    def wftool(self):
        return getToolByName(self.context, 'portal_workflow')

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    # Get valid people brain objects (cached)
    def getValidPeople(self):

        cache = IAnnotations(self.request)
        key = self.get_key()

        if not cache.has_key(key):
            cache[key] = self._getValidPeople()

        return cache[key]

    # Get agComm People
    @property
    def agcomm_people(self):
        grouptool = getToolByName(self.context, 'portal_groups')
        group = grouptool.getGroupById('agcomm') # Hard-coded group name

        if group:
            people_ids = group.getGroupMemberIds()

            if people_ids:

                rv = self.portal_catalog.searchResults({
                    'Type' : 'Person',
                    'getId' : people_ids,
                    'sort_on' : 'sortable_title',
                })

                return list(rv)

        return []

    # Get valid people brain objects (Uncached)
    def _getValidPeople(self):
        review_state = [self.active_review_state, self.inactive_review_state]

        if self.active:
            review_state = [self.active_review_state, ]

        # Get valid people objects
        rv = list(self.portal_catalog.searchResults({
            'Type' : 'Person',
            'review_state' : review_state,
            'sort_on' : 'sortable_title',
        }))

        _ids = set([x.getId for x in rv])

        # Ag Comm people are always valid
        rv.extend([x for x in self.agcomm_people if x.getId not in _ids])

        return rv

    @memoize
    def getPersonIdToBrain(self):
        return dict([(x.getId, x) for x in self.getValidPeople()])

    def getPersonById(self, _id):
        return self.getPersonIdToBrain().get(_id, None)

    def getValidPeopleIds(self):
        return [x.getId for x in self.getValidPeople()]

    # Active people who are expired.
    @property
    def expired_active_people(self):

        return self.portal_catalog.searchResults({
            'Type' : 'Person',
            'review_state' : self.active_review_state,
            'expires' : {
                'range' : 'max',
                'query': DateTime()
            },
            'sort_on' : 'sortable_title',
        })

    def by_classification(self, classification=None):
        rv = []

        for r in self.getValidPeople():
            v = r.Classifications

            if isinstance(v, (list, tuple)):
                if classification in v:
                    rv.append(r)

        return rv

    @property
    def tmc(self):
        return self.by_classification("Team Marketing Coordinator")

# This makes the 'getURL' and 'absolute_url', etc. methods return the proper
# URL through the debug prompt.
def setSiteURL(site, domain='cms.extension.psu.edu', path='', https=True):

    if path and not path.startswith('/'):
        path = '/%s' % path

    if https:
        url = 'https://%s%s' % (domain, path)
    else:
        url = 'http://%s%s' % (domain, path)

    if url.endswith('/'):
        url = url[:-1]

    site.REQUEST['SERVER_URL'] = url

    site.REQUEST.other['VirtualRootPhysicalPath'] = site.getPhysicalPath()

    if site.REQUEST.get('_ec_cache', None):
        site.REQUEST['_ec_cache'] = {}

# Recursively traverses schema parent classes, and returns a complete list of schemas
def getAllSchemas(schema=None):

    # If none is provided, use the object for this schema dump
    if not schema:
        return []

    # List to return
    schemas = []

    # Only include this schema if it has fields
    if schema.names():
        schemas.append(schema)

    # Traverse upwards through the bases, and add them
    for _s in schema.getBases():
        schemas.extend(getAllSchemas(_s))

    return schemas

# Returns a list of field names that includes all fields from base (parent)
# schemas recursively.
def getAllSchemaFields(schema=None):

    names_descriptions = getAllSchemaFieldsAndDescriptions(schema)
    return [x[0] for x in names_descriptions]

# Returns a list of field names that includes all fields from base (parent)
# schemas recursively.  It's turtles all the way down.
def getAllSchemaFieldsAndDescriptions(schemas=None):

    names = []
    names_descriptions = []

    if not isinstance(schemas, (list, tuple)):
        schemas = [schemas,]

    for schema in schemas:
        for s in getAllSchemas(schema):
            for (n, d) in s.namesAndDescriptions():

                # Skip methods on schema
                if isinstance(d, Method):
                    continue

                if n not in names:
                    names.append(n)
                    names_descriptions.append((n, d))

    return names_descriptions

# Base Dexterity Schema
# From http://docs.plone.org/develop/plone/forms/schemas.html#id8
def getBaseSchemaForType(portal_type):

    try:
        schema = getUtility(IDexterityFTI, name=portal_type).lookupSchema()
    except ComponentLookupError:
        pass
    else:
        if schema:
            return schema

    return Interface

def getBehaviorSchemasForType(portal_type):

    schemas = []

    try:
        behaviors = getUtility(IDexterityFTI, name=portal_type).behaviors
    except ComponentLookupError:
        pass
    else:

        if behaviors:
            for i in behaviors:
                try:
                    behavior = getUtility(IBehavior, name=i)
                except ComponentLookupError:
                    pass
                else:
                    if IFormFieldProvider.providedBy(behavior.interface):
                        schemas.append(behavior.interface)

    return schemas

def getBaseSchema(context):
    return getBaseSchemaForType(context.portal_type)

def getAllSchemaFieldsAndDescriptionsForType(portal_type):
    schemas = [getBaseSchemaForType(portal_type),]
    schemas.extend(getBehaviorSchemasForType(portal_type))
    return getAllSchemaFieldsAndDescriptions(schemas)

# Resize image to new dimensions.  This takes the 'blob' field for the image,
# checks to see if it falls within the dimensions, and scales it accordingly.
def rescaleImage(image, max_width=1200.0, max_height=1200.0, quality=100):

    img_value = scaleImage(image, max_width=max_width, max_height=max_height, quality=quality)

    if img_value:
        image._setData(img_value)
        return True

def scaleImage(image, max_width=1200.0, max_height=1200.0, quality=100):

    # Test the field to make sure it's a blob image
    if not isinstance(image, NamedBlobImage):
        raise TypeError(u'%r is not a NamedBlobImage field.' % image)

    (w,h) = image.getImageSize()

    image_format = IMAGE_FORMATS.get(image.contentType, [None, None])[0]

    ratio = min([float(max_width)/w, float(max_height)/h])

    if ratio < 1.0 or quality < 100:

        if ratio < 1.0:
            new_w = w * ratio
            new_h = h * ratio
        else:
            new_w = w
            new_h = h

        try:
            pil_image = Image.open(StringIO(image.data))
        except IOError:
            pass
        else:
            pil_image.thumbnail([new_w, new_h], Image.ANTIALIAS)

            img_buffer = StringIO()

            pil_image.save(img_buffer, image_format, quality=quality)

            return img_buffer.getvalue()


def getStoreViewId(context, internal=False, external=False):

    term = None

    if internal:
        term = 'Internal'
    elif external:
        term = 'External'

    if term:

        # Get the StoreViewId vocabulary
        vocab_factory = getUtility(IVocabularyFactory, "agsci.atlas.StoreViewId")
        vocab = vocab_factory(context)

        # Return vocab terms
        v = [x.value for x in vocab if x.title in [term,]]

        if v:
            return v[0]

def checkStore(context, internal=False, external=False):

    store_view_id = getattr(context, 'store_view_id', [])
    find_store_view_id = getStoreViewId(context, internal=internal, external=external)

    if isinstance(store_view_id, (list, tuple)):
        return find_store_view_id in store_view_id

def isInternalStore(context):
    return checkStore(context, internal=True)

def isExternalStore(context):
    return checkStore(context, external=True)

def generate_sku_regex(skus=[]):

    skus = set([x for x in skus if x])

    _ = [x.split('-') for x in skus]

    data = {}
    values = []

    for x in _:
        j = x.pop()
        i = "-".join(x)
        if not data.has_key(i):
            data[i] = []
        data[i].append(j)

    for (k,v) in sorted(data.iteritems()):

        prefix = ""

        if k:
            prefix = "%s-" % k

        if len(v) > 1:
            values.append(
                "%s(%s)" % (prefix, "|".join(sorted(v)))
            )

        else:
            values.append("%s%s" % (prefix, v[0]))

    return "^(" + "|".join(values) + ")$"

def get_web_users():

    # Get the members of the AgComm group
    grouptool = getToolByName(getSite(), 'portal_groups')
    agCommGroup = grouptool.getGroupById("agcomm")

    _ = agCommGroup.getGroupMemberIds()

    # Append hardcoded list of people who were previously AgComm folks
    _.extend([
        'aln',
        'cmk176',
        'cjm49',
        'rad2',
        'gra104',
        'mds118',
        'kck12',
        'pgw105',
        'aby104',
        'sed5047',
    ])

    return _

def get_last_modified_by_content_owner(context):

    try:
        web_users = get_web_users()
    except WorkflowException:
        pass
    else:
        if web_users:

            v = ContentHistoryViewlet(context, getRequest(), None, None)

            v.navigation_root_url = v.site_url = CMS_DOMAIN

            history = v.fullHistory()

            if history:

                for _ in history:
                    actor = _.get('actor', {})
                    username = actor.get('username', '')
                    fullname = actor.get('fullname', '')
                    if username and username not in web_users:
                        return (username, fullname, DateTime(_['time']))

    return (None, None, None)

# Stolen from from Products.CMFPlone.CatalogTool.getObjSize
def get_human_file_size(size):

    smaller = SIZE_ORDER[-1]

    # if the size is a float, then make it an int
    # happens for large files
    try:
        size = int(size)
    except (ValueError, TypeError):
        pass

    if not size:
        return '0 %s' % smaller

    if isinstance(size, (int, long)):

        if size < SIZE_CONST[smaller]:
            return '1 %s' % smaller

        for c in SIZE_ORDER:
            if size / SIZE_CONST[c] > 0:
                break

        return '%.1f %s' % (float(size / float(SIZE_CONST[c])), c)

    return size

def get_internal_store_categories():

    mc = AtlasMetadataCalculator('CategoryLevel1')
    return mc.getInternalStoreTerms()

def has_internal_store_categories(context):

    l1 = getattr(aq_base(context), 'atlas_category_level_1', [])

    if l1:

        internal_l1 = get_internal_store_categories()
        return not not [x for x in l1 if x in internal_l1]

def get_zope_root():
    INSTANCE_HOME=os.environ.get('INSTANCE_HOME', '')
    _ = INSTANCE_HOME.split('/')
    return "/".join(_[0:_.index('zeocluster')+1])

zope_root = get_zope_root()