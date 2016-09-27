from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from datetime import datetime
from plone.memoize.instance import memoize
from zope.component.hooks import getSite

import pytz
import base64

# Naively assume that all dates are in Eastern time
default_timezone = 'US/Eastern'

# Convert an ISO date string to a datetime with the UTC timezone
def iso_to_datetime(v):
    try:
        zope_date_value = DateTime(v)
        dt = pytz.utc.localize(zope_date_value.toZone(default_timezone).utcdatetime())
        return dt.replace(tzinfo=pytz.utc)
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

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    # Get valid people brain objects
    @memoize
    def getValidPeople(self):
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
