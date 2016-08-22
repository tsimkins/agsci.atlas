from BeautifulSoup import BeautifulSoup
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer

from urlparse import urljoin

import re

from .base import BaseImportContentView

from agsci.atlas.content.sync import external_reference_tags
from agsci.atlas.content.sync.product import AtlasProductImporter
from agsci.atlas.content.sync.mapping import mapCategories as _mapCategories

# Regular expression to validate UID
uid_re = re.compile("^[0-9abcedf]{32}$", re.I|re.M)

class ImportProductView(BaseImportContentView):

    # Get UID from request
    @property
    def uid(self):
        return self.request.form.get('UID', None)

    def requestValidation(self):

        if not self.uid:
            raise ValueError('No UID provided')

        # Validate UID
        if not uid_re.match(self.uid):
            raise ValueError('Invalid UID "%s"' % self.uid)

        return True

    # Get mapped categories.  This is passed a list of lists (programs/topics)
    def mapCategories(self, *args):

        old_categories = []

        for i in args:
            old_categories.extend(i)

        return _mapCategories(self.import_path, old_categories)

    def createProduct(self, context, product_type, v, **kwargs):

        # Get new categories from existing ones.
        categories = self.mapCategories(v.data.extension_topics, v.data.extension_subtopics)

        # Add categories to keyword arguments
        kwargs.update(categories)

        item = createContentInContainer(
                context,
                product_type,
                id=self.getId(v),
                title=v.data.title,
                description=v.data.description,
                owners=v.data.creators,
                authors=v.data.contributors,
                **kwargs)

        # Add leadimage to item
        if v.data.has_content_lead_image:
            item.leadimage = v.data_to_image_field(v.data.leadimage,
                                                   v.data.leadimage_content_type,
                                                   v.data.leadimage_filename)
            item.leadimage_caption = v.data.image_caption

        return item

    # Adds an Article object given a context and AtlasProductImporter
    def addArticle(self, context, v, **kwargs):

        # Create parent article
        article = self.createProduct(context, 'atlas_article', v, **kwargs)

        # Add an article page with the text of the article object
        self.addArticlePage(article, v)

        return article

    # Adds an Article Page inside an Article given a context and AtlasProductImporter
    def addArticlePage(self, context, v):

        # If we're a Photo Folder, create a Slideshow. This handles cases where
        # the top-level 'Article' is really a slideshow.  Then, an Article with
        # a slideshow will be created.
        if v.data.type in ('Photo Folder',):
            page = self.addSlideshow(context, v)

        # Otherwise, add a page to the article and set text
        else:
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
                _v = AtlasProductImporter(uid=i)

                if _v.data.type in ('Page', 'Folder'): # Content-ception
                    self.addArticlePage(context, _v)

                elif _v.data.type in ('File',):
                    self.addFile(context, _v)

                elif _v.data.type in ('Link',):
                    self.addLink(context, _v)

                elif _v.data.type in ('Photo Folder',):
                    self.addSlideshow(context, _v)


        return page

    # Adds an Image object given a context and AtlasProductImporter
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

    # Adds a File object given a context and AtlasProductImporter
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

    # Adds a Link object given a context and AtlasProductImporter
    def addLink(self, context, v):

        item = createContentInContainer(
                    context,
                    "Link",
                    id=self.getId(v),
                    title=v.data.title,
                    description=v.data.description,
                    remoteUrl=v.data.get_remote_url
                    )

        return item


    def addSlideshow(self, context, v):

        item = createContentInContainer(
                    context,
                    "atlas_article_slideshow",
                    id=self.getId(v),
                    title=v.data.title,
                    description=v.data.description,
                    )

        # Add slideshow html as page text
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        # Add images to slideshow
        for i in v.data.contents:
            _v = AtlasProductImporter(uid=i)

            if _v.data.type in ('Image',):
                self.addImage(item, _v)

        return item

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
            v = AtlasProductImporter(url=url)

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


class ImportArticleView(ImportProductView):

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid)

        # Add an article
        item = self.addArticle(self.import_path, v)

        # Return JSON output
        return self.getJSON(item)


class ImportPublicationView(ImportProductView):

    # Adds a Publication object given a context and AtlasProductImporter
    def addPublication(self, context, v, **kwargs):

        # Create publication
        return self.createProduct(context, 'atlas_publication', v, **kwargs)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid)

        # Additional fields
        kwargs = {}

        # Publication code as SKU
        kwargs['sku'] = v.data.extension_publication_code

        # Convert price to float, and swallow exception if it fails
        try:
            kwargs['price'] = float(v.data.extension_publication_cost)
        except (ValueError, TypeError):
            pass

        # Add a publication
        item = self.addPublication(self.import_path, v, **kwargs)

        # If the publication has body text, add it as the 'text' field.
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        # Return JSON output
        return self.getJSON(item)
