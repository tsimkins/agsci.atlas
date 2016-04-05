from BeautifulSoup import BeautifulSoup
from Products.Five import BrowserView
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer import idnormalizer
from plone.registry.interfaces import IRegistry
from zope.component.hooks import getSite
from zope.component import getUtility
from zope.interface import Interface, alsoProvides
from .. import AtlasContentImporter, external_reference_tags
from ..mapping import mapCategories as _mapCategories
import re
import urllib2
from urlparse import urljoin

try:

    from plone.protect.interfaces import IDisableCSRFProtection

except ImportError:

    class IDisableCSRFProtection(Interface):
        pass

# Regular expression to validate UID
uid_re = re.compile("^[0-9abcedf]{32}$", re.I|re.M)

class ImportContentView(BrowserView):

    @property
    def registry(self):
        return getUtility(IRegistry)
        
    # Checks to see if remote IP not in 'agsci.atlas.import.allowed_ip' list.
    def remoteIPAllowed(self):
    
        remote_ip = self.request.get('REMOTE_ADDR')

        allowed_ip = self.registry.get('agsci.atlas.import.allowed_ip')
        
        return remote_ip and (remote_ip in allowed_ip)

    # Get UID from request
    @property
    def uid(self):
        return self.request.form.get('UID', None)

    # Get import path from registry
    @property
    def import_path(self):
        path = self.registry.get('agsci.atlas.import.path')

        if path.startswith('/'):
            path = path[1:]

        return getSite().restrictedTraverse(path)

    def __call__(self):

        # Validate IP
        if not self.remoteIPAllowed():
            raise Exception('IP "%s" not permitted to import content.' % remote_ip)
   
        # Validate UID
        if not uid_re.match(self.uid):
            raise ValueError('Invalid UID "%s"' % self.uid)

        # Override CSRF protection so we can make changes from a GET
        #
        # Controls: 
        #   * Remote IP checked against ACL
        #   * UID checked for valid format via regex.
        #   * Importer class points to pre-determined URL for JSON data
        alsoProvides(self.request, IDisableCSRFProtection)
        
        return self.importContent()

    # Get mapped categories.  This is passed a list of lists (programs/topics)
    def mapCategories(self, *v):
    
        old_categories = []
        
        for i in v:
            old_categories.extend(i)
    
        return _mapCategories(self.import_path, old_categories)        

    # Performs the import of content by creating an AtlasContentImporter object
    # and using that data  to create the content.
    def importContent(self):
        return "Generic view, nothing created."

    # Returns normalized id of title
    def getId(self, v):
        return idnormalizer.normalize(v.data.title)

    def createProduct(self, context, product_type, v):

        # Get new categories from existing ones.
        categories = self.mapCategories(v.data.extension_topics, v.data.extension_subtopics)

        item = createContentInContainer(
                context, 
                product_type, 
                id=self.getId(v), 
                title=v.data.title, 
                description=v.data.description,
                owners = v.data.creators,
                contacts = v.data.contributors,
                authors = v.data.contributors,
                **categories)

        # Add leadimage to item
        if v.data.has_content_lead_image:
            item.leadimage = v.data_to_image_field(v.data.leadimage, 
                                                   v.data.leadimage_content_type, 
                                                   v.data.leadimage_filename)
            item.leadimage_caption = v.data.image_caption

        return item

    # Adds an image object given a context and AtlasContentImporter
    def addImage(self, context, v):

        item = createContentInContainer(
                    context, 
                    "Image", 
                    id=self.getId(v), 
                    title=v.data.title, 
                    description=v.data.description)

        data = v.get_binary_data(v.data.url)

        filename=data[2]
        
        if not filename:
            filename = self.getId(v)

        item.image = v.data_to_image_field(data=data[0], contentType=data[1], filename=filename)
        
        return item

    # Adds a file object given a context and AtlasContentImporter
    def addFile(self, context, v):

        item = createContentInContainer(
                    context, 
                    "File", 
                    id=self.getId(v), 
                    title=v.data.title, 
                    description=v.data.description)

        data = v.get_binary_data(v.data.url)
        
        filename=data[2]
        
        if not filename:
            filename = self.getId(v)
        
        item.file = v.data_to_file_field(data=data[0], contentType=data[1], filename=filename)
        
        return item

    def addLink(self, context, v):
        return False

    def addSlideshow(self, context, v):
        return False

    # Get images referenced by object and upload them inside parent object.
    def addImagesFromBodyText(self, context, v):
    
        patterns = ['/image_', ]
    
        return self.addResourcesFromBodyText(context, v=v, resource_type='Image', 
                                             urls=v.data.img, patterns=patterns,
                                             create_method=self.addImage)
                                             
    # Get files referenced by object and upload them inside parent object.
    def addFilesFromBodyText(self, context, v):
    
        patterns = ['/view', '/at_download/file']
    
        return self.addResourcesFromBodyText(context, v=v, resource_type='File', 
                                             urls=v.data.a, patterns=patterns,
                                             create_method=self.addFile)
        
    # Get items referenced by object and upload them inside parent object.
    def addResourcesFromBodyText(self, context, v=None, resource_type='Image', 
                                 urls=[], patterns=[], 
                                 create_method=None):

        # Dict to hold from/to replacements
        replacements = {}

        # Loop through resources pulled from HTML
        for url in urls:

            # URL of resource (so we can modify it without affecting the original)
            original_url = url
            
            # Don't replace if it's an HTTP URL to an external site.
            # If it doesn't start with http, calculate an absolute URL with
            # urljoin
            if url.startswith('http'):
                if not url.startswith(v.root_url):
                    continue
            else:
                url = urljoin(v.url, url)
            
            # Strip off specified patterns from end of URL.
            # Sort patterns for the largest first.
            for p in sorted(patterns, key=lambda x: len(x), reverse=True):

                url_pattern_index = url.rfind(p)
                
                if url_pattern_index >= 0:
                    url = url[:url_pattern_index]
            
            # Get API data for resource
            v = AtlasContentImporter(url=url)
            
            # Confirm we're a valid resource_type
            try:
                # If we're not a valid resource_type in Plone, continue
                # to the next item
                if v.data.type != resource_type:
                    continue
            except:
                # If we get an error (e.g. bad URL, etc.) just continue.
                # We'll clean it up in post.
                continue

            # Now that we know we have a valid resource, we're going to create
            # it as a Plone resource inside the object
            if create_method:
                item = create_method(context, v)

            # Add new resource URL to replacements dict
            replacements[original_url] = 'resolveuid/%s' % item.UID()

        # Return replacements dict.  Caller will use this to modify HTML
        return replacements

    # Takes HTML code and a dictionary of replacements
    # Iterates through images (<img>) and links (<a>) and replaces src/href
    # attributes if the replacement dictionary contains a replacement.
    def replaceURLs(self, html='', replacements={}):

        # Replace '<img src="..." />' and '<a href="...">' with new URL in HTML
        soup = BeautifulSoup(html)
        
        for (i,j) in external_reference_tags:
        
            for k in soup.findAll(i):
                url = k.get(j, '')
    
                if url:
                    k[j] = replacements.get(url, url)

        return repr(soup)

class ImportArticleView(ImportContentView):

    # Performs the import of content by creating an AtlasContentImporter object
    # and using that data  to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasContentImporter(uid=self.uid)
        
        # Add an article
        article = self.addArticle(self.import_path, v)

        # Return article title
        return 'Created %s' % v.data.title

    def addArticle(self, context, v):
        
        # Create parent article
        article = self.createProduct(context, 'atlas_article', v)

        # Add an article page with the text of the article object
        self.addArticlePage(article, v)

        return article

    # Adds an article page inside an article
    def addArticlePage(self, context, v):
    
        # Add a page to the article and set text
        page = createContentInContainer(
                            context, 
                            "atlas_article_page", 
                            id=self.getId(v), 
                            title=v.data.title, 
                            description=v.data.description)

        # Get images and files referenced by article and upload them inside article.
        
        replacements = {}
        replacements.update(self.addImagesFromBodyText(context, v))
        replacements.update(self.addFilesFromBodyText(context, v))

        # Replace Image URLs in HTML with resolveuid/... links
        html = self.replaceURLs(v.data.html, replacements)

        # Add article html as page text
        page.text = RichTextValue(raw=html, 
                                  mimeType=u'text/html', 
                                  outputMimeType='text/x-html-safe')

        # If we're a multi-page article, go through the contents
        for i in v.data.contents:
            _v = AtlasContentImporter(uid=i)
            
            if _v.data.type in ('Page', 'Folder'): # Content-ception
                self.addArticlePage(context, _v)

            elif _v.data.type in ('File',): 
                self.addFile(context, _v)

            elif _v.data.type in ('Link',): 
                self.addLink(context, _v)
                
            elif _v.data.type in ('Photo Folder',): 
                self.addSlideshow(context, _v)


        return page










