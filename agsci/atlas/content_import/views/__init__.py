from Products.Five import BrowserView
from .. import AtlasContentImporter
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer import idnormalizer
from zope.interface import Interface
from zope.interface import alsoProvides
from plone.app.textfield.value import RichTextValue

try:

    from plone.protect.interfaces import IDisableCSRFProtection

except ImportError:

    class IDisableCSRFProtection(Interface):
        pass
    

class ImportContentView(BrowserView):

    def __call__(self):
        
        alsoProvides(self.request, IDisableCSRFProtection)
        
        uid = self.request.form.get('UID', None)
        
        if uid:
            v = AtlasContentImporter(uid)
            
            # Check for UID to see if we got anything.
            if not v.data.uid:
                return "Invalid UID provided."    
            
            # Go ahead and do the import
            import_path = v.import_path
            
            # Content id
            _id = idnormalizer.normalize(v.data.title)
            
            # Create parent article
            article = createContentInContainer(import_path, "atlas_article", id=_id, title=v.data.title, description=v.data.description)

            article_page = createContentInContainer(article, "atlas_article_page", id=_id, title=v.data.title, description=v.data.description)

            article_page.text = RichTextValue(raw=v.data.html, 
                                              mimeType=u'text/html', 
                                              outputMimeType='text/x-html-safe')

            title = v.data.title
            
            return 'Created %s' % title
            
        return "No UID provided."
