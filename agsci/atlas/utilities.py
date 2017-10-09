from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser
from Acquisition import aq_base
from DateTime import DateTime
from PIL import Image
from Products.CMFCore.utils import getToolByName
from StringIO import StringIO
from datetime import datetime
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from plone.dexterity.interfaces import IDexterityFTI
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
import re

from .constants import DEFAULT_TIMEZONE, IMAGE_FORMATS
from .content.article import IArticle
from .content.slideshow import ISlideshow

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

def encode_blob(f, show_data=True):
    data = getattr(f, 'data', None)
    if data:
        if show_data:
            return (getContentType(f), base64.b64encode(data))
        return (getContentType(f), '')
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
    if hasattr(_context, 'text') and hasattr(_context, 'raw'):
        if _context.text.raw:
            html = _context.text.raw

    # Handle a slideshow by addin ga paragraph per image.
    if ISlideshow.providedBy(context):

        for img in ISlideshowMarker(context).getImages():

            title = img.Title().decode('utf-8')
            description = img.Description().decode('utf-8')
            uid = img.UID()

            _html = u"""<img src="resolveuid/%s" /><br />""" % uid
            _html = _html + u"""<strong>%s</strong>""" % title

            if description:
                _html = _html + u"""<br />%s""" % description

            _html = u"""<p class="discreet">""" + _html + "</p>"

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

    return html


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
def ploneify(toPlone):
    ploneString = re.sub("[^A-Za-z0-9]+", "-", toPlone).lower()
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
                })

                return list(rv)

        return []

    # Get valid people brain objects (Uncached)
    def _getValidPeople(self):
        review_state = ['published', 'published-inactive']

        if self.active:
            review_state = ['published', ]

        # Get valid people objects
        rv = list(self.portal_catalog.searchResults({
            'Type' : 'Person',
            'review_state' : review_state,
        }))

        # Ag Comm people are always valid
        rv.extend(self.agcomm_people)

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
            'review_state' : 'published',
            'expires' : {
                'range' : 'max',
                'query': DateTime()
            }
        })

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
def rescaleImage(image, max_width=1200.0, max_height=1200.0):

    # Test the field to make sure it's a blob image
    if not isinstance(image, NamedBlobImage):
        raise TypeError(u'%r is not a NamedBlobImage field.' % image)

    (w,h) = image.getImageSize()

    image_format = IMAGE_FORMATS.get(image.contentType, [None, None])[0]

    ratio = min([float(max_width)/w, float(max_height)/h])

    if ratio < 1.0:
        new_w = w * ratio
        new_h = h * ratio

        try:
            pil_image = Image.open(StringIO(image.data))
        except IOError:
            pass
        else:
            pil_image.thumbnail([new_w, new_h], Image.ANTIALIAS)

            img_buffer = StringIO()

            pil_image.save(img_buffer, image_format, quality=100)

            img_value = img_buffer.getvalue()

            image._setData(img_value)

            return True

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