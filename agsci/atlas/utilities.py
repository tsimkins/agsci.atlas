from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from datetime import datetime
from dateutil import parser as date_parser
from plone.dexterity.interfaces import IDexterityFTI
from plone.memoize.instance import memoize
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.component.interfaces import ComponentLookupError
from zope.interface import Interface
from zope.globalrequest import getRequest

import pytz
import base64
import re

# Naively assume that all dates are in Eastern time
default_timezone = 'US/Eastern'

# Convert an ISO date string to a datetime with the UTC timezone
def iso_to_datetime(v):
    try:
        # Parse the date
        dt = date_parser.parse(v)

        # Check for naive timezone, and assign to Eastern if it is
        # Ref http://stackoverflow.com/questions/5802108/how-to-check-if-a-datetime-object-is-localized-with-pytz
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            dt = pytz.timezone(default_timezone).localize(dt)

        # Return the dt object
        return dt
    except:
        return None

# Convert a Plone DateTime to a ISO formated string
def toISO(v):

    if isinstance(v, DateTime):
        try:
            tz = pytz.timezone(v.timezone())
        except pytz.UnknownTimeZoneError:
            # Because that's where we are.
            tz = pytz.timezone(default_timezone)

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
        v = getattr(i,j,None)
        if v:
            if hasattr(v, '__call__'):
                return v()
            else:
                return v
    return None

def increaseHeadingLevel(text):
    if '<h2' in text:
        for i in reversed(range(1,6)):
            from_header = "h%d" % i
            to_header = "h%d" % (i+1)
            text = text.replace("<%s" % from_header, "<%s" % to_header)
            text = text.replace("</%s" % from_header, "</%s" % to_header)
    return text

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

    def __init__(self):
        self.context = getSite()

    def get_key(self):
        return "-".join([self.__class__.__name__])

    @property
    def request(self):
        return getRequest()

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

    # Get valid people brain objects (Uncached)
    def _getValidPeople(self):
        return self.portal_catalog.searchResults({'Type' : 'Person',
                                             'expires' : {'range' : 'min',
                                                          'query': DateTime()
                                                         }
                                             })

    @memoize
    def getPersonIdToBrain(self):
        return dict([(x.getId, x) for x in self.getValidPeople()])

    def getPersonById(self, _id):
        return self.getPersonIdToBrain().get(_id, None)

    def getValidPeopleIds(self):
        return [x.getId for x in self.getValidPeople()]

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

# Base Dexterity Schema
# From http://docs.plone.org/develop/plone/forms/schemas.html#id8
def getBaseSchema(context):

    try:
        schema = getUtility(IDexterityFTI, name=context.portal_type).lookupSchema()
    except ComponentLookupError:
        pass
    else:
        if schema:
            return schema

    return Interface