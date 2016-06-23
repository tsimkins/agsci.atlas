from Products.Five import BrowserView
from ..cvent import CventContentImporter
from zope.interface import alsoProvides
from . import ImportContentView

try:

    from plone.protect.interfaces import IDisableCSRFProtection

except ImportError:

    class IDisableCSRFProtection(Interface):
        pass


class ImportCventView(ImportContentView):

    def __call__(self):

        # Validate IP
        if not self.remoteIPAllowed():
            raise Exception('IP "%s" not permitted to import content.' % self.remote_ip)
   
        # Override CSRF protection so we can make changes from a GET
        #
        # Controls: 
        #   * Remote IP checked against ACL
        #   * UID checked for valid format via regex.
        #   * Importer class points to pre-determined URL for JSON data
        alsoProvides(self.request, IDisableCSRFProtection)
        
        import pdb; pdb.set_trace()