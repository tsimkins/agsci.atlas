from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from plone.dexterity.interfaces import IDexterityContent
from plone.i18n.normalizer import idnormalizer
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import Interface, alsoProvides

from ..user import execute_under_special_role

# Create dummy IDisableCSRFProtection interface if plone.protect isn't installed.
try:

    from plone.protect.interfaces import IDisableCSRFProtection

except ImportError:

    class IDisableCSRFProtection(Interface):
        pass

# Generic view for importing content
class ImportContentView(BrowserView):

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

    # This method is run when the view is called.
    def __call__(self):

        # Validate IP
        if not self.remoteIPAllowed():
            raise Exception('IP "%s" not permitted to import content.' % self.remote_ip)

        # Any additional request validation
        if not self.requestValidation():
            raise Exception('Request validation failed.')

        # Override CSRF protection so we can make changes from a GET
        #
        # Controls:
        #   * Remote IP checked against ACL
        #   * UID checked for valid format via regex.
        #   * Importer class points to pre-determined URL for JSON data
        alsoProvides(self.request, IDisableCSRFProtection)

        # Set headers for no caching, and JSON content type
        self.setHeaders()

        # Running importContent as Contributor so we can do this anonymously.
        return execute_under_special_role(getSite(), ['Contributor', 'Reader', 'Editor'], self.importContent)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data  to create the content.
    def importContent(self):

        return json.dumps({'error' : 'Generic view, nothing created.'})

    def setHeaders(self):
        # Prevent from being cached in proxy cache
        self.request.response.setHeader('Pragma', 'no-cache')
        self.request.response.setHeader('Cache-Control', 'private, no-cache, no-store, max-age=0, must-revalidate, proxy-revalidate')

        # Set to JSON content type
        self.request.response.setHeader('Content-Type', 'application/json')

    # Returns normalized id of title
    def getId(self, v):
        return idnormalizer.normalize(v.data.title)

    def getJSON(self, context):
        if IDexterityContent.providedBy(context):
            self.request.form['bin'] = 'False'
            self.request.form['recursive'] = 'False'
            return context.restrictedTraverse('@@api').getJSON()

        # Return jsonified data
        return json.dumps({'error_message' : 'Error: %s' % repr(item)})