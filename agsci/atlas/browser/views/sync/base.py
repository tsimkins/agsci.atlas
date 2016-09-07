from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from plone.dexterity.interfaces import IDexterityContent
from plone.i18n.normalizer import idnormalizer
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import Interface, alsoProvides
from zLOG import LOG, INFO, ERROR
from agsci.common.utilities import execute_under_special_role
from agsci.atlas.content.sync.mapping import mapCategories as _mapCategories

import json

# Create dummy IDisableCSRFProtection interface if plone.protect isn't installed.
try:

    from plone.protect.interfaces import IDisableCSRFProtection

except ImportError:

    class IDisableCSRFProtection(Interface):
        pass

# Generic view for importing content
class BaseImportContentView(BrowserView):

    @property
    def registry(self):
        return getUtility(IRegistry)

    # Returns IP of browser making request.
    # http://docs.plone.org/develop/plone/serving/http_request_and_response.html#id11
    # Better than how I was doing it.

    @property
    def remote_ip(self):

        ip = None

        if "HTTP_X_FORWARDED_FOR" in self.request.environ:
            # Virtual host
            ip = self.request.environ["HTTP_X_FORWARDED_FOR"]

            # If ip format is 'x, y', return x.
            if ', ' in ip:
                ip = ip.split(', ')[0]

        elif "HTTP_HOST" in self.request.environ:
            # Non-virtualhost
            ip = self.request.environ["REMOTE_ADDR"]

        return ip

    # Checks to see if remote IP not in 'agsci.atlas.import.allowed_ip' list.
    def remoteIPAllowed(self):

        allowed_ip = self.registry.get('agsci.atlas.import.allowed_ip')

        return self.remote_ip and (self.remote_ip in allowed_ip)

    # Get import path from registry
    @property
    def import_path(self):
        path = self.registry.get('agsci.atlas.import.path')

        if path.startswith('/'):
            path = path[1:]

        return getSite().restrictedTraverse(path)

    # Do any additional checks. For base class, this just returns True as a NOOP.
    def requestValidation(self):
        return True

    # Returns the portal catalog object
    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    def HTTPError(self, v):
        self.log("500: API Error: %s" % v, ERROR)
        self.request.response.setStatus(500, reason='API Error', lock=True)
        self.request.response.setHeader('Content-Type', 'text/plain')
        return v

    # This method is run when the view is called.
    def __call__(self):

        # Validate IP
        if not self.remoteIPAllowed():
            return self.HTTPError('IP "%s" not permitted to import content.' % self.remote_ip)

        # Any additional request validation
        try:
            if not self.requestValidation():
                return self.HTTPError('Request validation failed.')
        except Exception as e:
            return self.HTTPError(e.message)

        # Override CSRF protection so we can make changes from a GET
        #
        # Controls:
        #   * Remote IP checked against ACL
        #   * UID checked for valid format via regex.
        #   * Importer class points to pre-determined URL for JSON data
        alsoProvides(self.request, IDisableCSRFProtection)

        # If a debug variable is not passed, swallow the exception and return it in the HTTP status
        if not self.request.form.get('debug', False):

            try:
                # Running importContent as Contributor so we can do this anonymously.
                return execute_under_special_role(['Contributor', 'Reader', 'Editor', 'Member'],
                                                  self.importContent)
            except Exception as e:
                return self.HTTPError('%s: %s' % (type(e).__name__, e.message))

        # Otherwise, throw the raw exception
        else:
            # Running importContent as Contributor so we can do this anonymously.
            return execute_under_special_role(['Contributor', 'Reader', 'Editor', 'Member'],
                                               self.importContent)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data  to create the content.
    def importContent(self):

        return json.dumps({'error' : 'Generic view, nothing created.'})

    def setHeaders(self):
        # Prevent from being cached in proxy cache
        self.request.response.setHeader('Pragma', 'no-cache')
        self.request.response.setHeader('Cache-Control', 'private, no-cache, no-store')

        # Set to JSON content type
        self.request.response.setHeader('Content-Type', 'application/json')

    # Returns normalized id of title
    def getId(self, v):
        return idnormalizer.normalize(v.data.title)

    # Returns the raw data (pre-JSON, but otherwise processed) for an item
    def getRawData(self, context):

        if IDexterityContent.providedBy(context):
            # Set content type and no caching headers
            self.setHeaders()

            # Pre-fill request parameters so we don't get the binary data or the
            # contents
            self.request.form['bin'] = 'False'
            self.request.form['recursive'] = 'False'

            # Render the @@api view for the item
            return context.restrictedTraverse('@@api').getData()
        
        return {'error_message' : 'Error: %s' % repr(context)}
            
    # Returns the JSON export for the content
    def getJSON(self, context):
        data = []
            
        if isinstance(context, list):
            for i in context:
                data.append(self.getRawData(i))
        else:
            data = self.getRawData(context)

        return json.dumps(data, indent=4, sort_keys=True)

    # Get mapped categories.  This is passed a list of lists (programs/topics)
    def mapCategories(self, *args):

        old_categories = []

        for i in args:
            old_categories.extend(i)

        return _mapCategories(self.import_path, old_categories)

    # Log messages to Zope log
    def log(self, msg, klass=INFO):
        subsystem = '%s (IP: %s)' % (self.__class__.__name__, self.remote_ip)
        LOG(subsystem, klass, msg)
