from BeautifulSoup import BeautifulSoup
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.event.interfaces import IEventAccessor

from urlparse import urljoin

import base64
import re
import urllib2

from .base import BaseImportContentView

from agsci.atlas.content.adapters import LocationAdapter
from agsci.atlas.content.behaviors import isUniqueSKU
from agsci.atlas.content.sync import external_reference_tags
from agsci.atlas.content.sync.product import AtlasProductImporter
from agsci.atlas.utilities import execute_under_special_role

# Regular expression to validate UID
uid_re = re.compile("^[0-9abcedf]{32}$", re.I|re.M)

# Video Regular Expressions
youtube_embed_re = re.compile("^\s*(?:https*:*)*//www.youtube.com/embed/([A-Za-z0-9_-]{0,12})\?*.*?\s*$", re.I|re.M)

video_regexes = [
    youtube_embed_re,
]

class ImportProductView(BaseImportContentView):

    # Get UID from request
    @property
    def uid(self):
        return self.request.form.get('UID', None)

    # Get Domain from request. Ensure this is a psu.edu domain.
    @property
    def domain(self):
        domain = self.request.form.get('domain', None)

        if domain and not domain.endswith('psu.edu'):
            raise Exception('Attempting to import from a non-psu.edu domain: %s' % domain)

        return domain

    # Search catalog for original Plone UID
    def getObjectByOriginalPloneId(self, uid):

        results = self.portal_catalog.searchResults({'OriginalPloneIds' : uid})

        if results:
            return results[0].getObject()

    def requestValidation(self):

        if not self.uid:
            raise ValueError('No UID provided')

        # Validate UID
        if not uid_re.match(self.uid):
            raise ValueError('Invalid UID "%s"' % self.uid)

        # Running getObjectByOriginalPloneId as someone with permission so it
        # will find content that's imported, but in a private state.
        imported_object = execute_under_special_role(['Contributor', 'Reader', 'Editor', 'Member'],
                                               self.getObjectByOriginalPloneId, self.uid)

        if imported_object:
            raise ValueError('UID %s already imported, at "%s"' % (self.uid, imported_object.absolute_url()))

        return True

    # Given a parent (context), product_type (e.g. Article), the importer
    # object, and other arguments, create a product of that type inside the container
    def createProduct(self, context, product_type, v, **kwargs):

        # Get new categories from existing ones.
        categories = self.mapCategories(v.data.extension_topics, v.data.extension_subtopics)

        # Add categories to keyword arguments
        kwargs.update(categories)

        # If there's a Plone UID from the old site, add that to original_plone_ids
        if v.data.uid:
            kwargs['original_plone_ids'] = [v.data.uid,]
            kwargs['original_plone_site'] = v.get_api_domain()

        # Only create the object if the SKU doesn't already exist.  The
        # isUniqueSKU method raises an Invalid() exception if the SKU exists.
        if isUniqueSKU(v.data.sku) and isUniqueSKU(kwargs.get('sku')):

            # Create product inside parent container
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

            # Set product workflow state to 'Requires Initial Review'
            wftool = getToolByName(context, 'portal_workflow')
            wftool.doActionFor(item, 'owner_review')

            item.reindexObject()
            item.reindexObjectSecurity()

            return item


    # Adds an Article object given a context and AtlasProductImporter
    def addArticle(self, context, v, **kwargs):

        # Log message
        self.log("Creating article %s" % v.data.title)

        # Create parent article
        article = self.createProduct(context, 'atlas_article', v, **kwargs)

        # Add an article page with the text of the article object
        self.addArticlePage(article, v)

        # Attach File
        download_pdf = v.data.extension_publication_file

        if download_pdf:
            pdf_data = base64.b64decode(download_pdf.get('data', ''))
            content_type = download_pdf.get('content_type', '')
            filename = download_pdf.get('filename', '')

            article.pdf_file = v.data_to_file_field(pdf_data,
                                                    contentType=str(content_type),
                                                    filename=filename)

        return article

    # Adds an Article Page inside an Article given a context and AtlasProductImporter
    def addArticlePage(self, context, v):

        page = None

        # Log message
        self.log("Creating article page %s" % v.data.title)

        # If we're a Photo Folder, create a Slideshow. This handles cases where
        # the top-level 'Article' is really a slideshow.  Then, an Article with
        # a slideshow will be created.
        if v.data.type in ('Photo Folder',):
            page = self.addSlideshow(context, v)

        # Otherwise, add a page to the article and set text
        else:

            # Only create the page if there's HTML
            if v.data.html:
                page = createContentInContainer(
                                    context,
                                    "atlas_article_page",
                                    id=self.getId(v),
                                    title=v.data.title,)

                # Get images and files referenced by article and upload them inside article.
                replacements = {}
                replacements.update(self.addImagesFromBodyText(context, v))
                replacements.update(self.addFilesFromBodyText(context, v))

                # Replace Image URLs in HTML with resolveuid/... links
                html = self.replaceURLs(v.data.html, replacements)

                # Add description text to HTML if it's different than the parent
                # container description
                if v.data.description != context.description:
                    description = "<p>%s</p>" % v.data.description
                    html = description + html

                # Add article html as page text
                page.text = RichTextValue(raw=html,
                                          mimeType=u'text/html',
                                          outputMimeType='text/x-html-safe')

            # If we're a multi-page article, go through the contents
            for i in v.data.contents:

                # Get the importer object based on the UID
                _v = AtlasProductImporter(uid=i, domain=self.domain)

                # If we have a review state, ensure that it's Atlas Ready
                # If not, skip the import for that object
                review_state = _v.data.review_state

                if review_state and review_state not in ['atlas-ready']:
                    continue

                # Based on the type, do the required import
                if _v.data.type in ('Page', 'Folder', 'Section', 'Subsite', 'HomePage'): # Content-ception
                    _item = self.addArticlePage(context, _v)

                    # If the page has a leadimage, upload it to the Article and prepend
                    # the HTML reference to the body text
                    leadimage_html = self.addLeadImageAsImage(context, _v)

                    if leadimage_html:
                        # Prepend and reset HTML
                        _html = leadimage_html + _item.text.raw
                        _item.text = RichTextValue(raw=_html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')


                elif _v.data.type in ('File',):
                    self.addFile(context, _v)

                elif _v.data.type in ('Link',):
                    self.addLink(context, _v)

                elif _v.data.type in ('Photo Folder',):
                    self.addSlideshow(context, _v)

        return page

    # Adds the Lead Image as an Image object given a context and AtlasProductImporter
    def addLeadImageAsImage(self, context, v):

        # Check for lead image
        if v.data.has_content_lead_image:
            # Log message
            self.log("Creating lead image as image %s" % v.data.title)

            image_data = v.data.leadimage
            content_type = v.data.leadimage_content_type
            filename = 'leadimage-%s' % self.getId(v)
            caption = v.data.image_caption
            title = 'LeadImage: %s' % v.data.title

            item = createContentInContainer(
                        context,
                        "Image",
                        id=self.getId(v),
                        title=title,
                        description=caption)

            item.image = v.data_to_image_field(v.data.leadimage, content_type, filename)

            fmt_data = {
                            'uid' : item.UID(),
                            'caption' : caption,
                            'title' : title,
            }

            if caption:
                return """
                    <p class="discreet">
                        <img src="resolveuid/%(uid)s"
                             alt="%(caption)s" /> <br />
                        %(caption)s
                    </p>
                """ % fmt_data
            else:
                return """
                    <p class="discreet">
                        <img src="resolveuid/%(uid)s"
                             alt="%(title)s" />
                    </p>
                """ % fmt_data

    # Adds an Image object given a context and AtlasProductImporter
    def addImage(self, context, v):

        # Log message
        self.log("Creating image %s" % v.data.title)

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
    def addFile(self, context, v, portal_type="File", **kwargs):

        # Log message
        self.log("Creating file %s" % v.data.title)

        item = createContentInContainer(
                    context,
                    portal_type,
                    id=self.getId(v),
                    title=v.data.title,
                    description=v.data.description,
                    **kwargs)

        data = v.get_binary_data(v.data.url)

        filename=data[2]

        if not filename:
            filename = self.getId(v)

        item.file = v.data_to_file_field(data=data[0], contentType=data[1], filename=filename)

        return item

    # Adds a Link object given a context and AtlasProductImporter
    def addLink(self, context, v):

        # Log message
        self.log("Creating link %s" % v.data.title)

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

        # Log message
        self.log("Creating slideshow %s" % v.data.title)

        item = createContentInContainer(
                    context,
                    "atlas_article_slideshow",
                    id=self.getId(v),
                    title=v.data.title,
                    )

        # Add slideshow html as page text
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        # Add images to slideshow
        for i in v.data.contents:
            _v = AtlasProductImporter(uid=i, domain=self.domain)

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
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Add an article
        item = self.addArticle(self.import_path, v)

        # Return JSON output
        return self.getJSON(item)


class ImportNewsItemView(ImportProductView):

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Add a news item
        item = self.addNewsItem(self.import_path, v)

        # Return JSON output
        return self.getJSON(item)

    # Adds an NewsItem object given a context and AtlasProductImporter
    def addNewsItem(self, context, v, **kwargs):

        # Log message
        self.log("Creating news item %s" % v.data.title)

        # Create parent news item
        item = self.createProduct(context, 'atlas_news_item', v, **kwargs)

        # If the news item has body text, add it as the 'text' field.
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        return item

class ImportPublicationView(ImportProductView):

    # Adds a Publication object given a context and AtlasProductImporter
    def addPublication(self, context, v, **kwargs):

        # Log message
        self.log("Creating publication %s" % v.data.title)

        # Create publication
        return self.createProduct(context, 'atlas_publication', v, **kwargs)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Additional fields
        kwargs = {}

        # Publication code as SKU
        kwargs['sku'] = v.data.extension_publication_code

        # If the page count is hardcoded.  Swallow exception for bad data
        if v.data.extension_override_page_count:
            try:
                kwargs['pages_count'] = int(v.data.extension_override_page_count)
            except:
                pass

        # Add a publication
        item = self.addPublication(self.import_path, v, **kwargs)

        # If the publication has body text, add it as the 'text' field.
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        # If this Publication is a "File" in the old system, attach that file
        # as a download or a sample depending on if that file is a sample
        if v.data.type in ['File', ]:

            # Create file blob field for file data
            file_req = urllib2.urlopen(v.data.url)
            file_data = file_req.read()
            file_content_type = file_req.headers.get('Content-type')

            file_field = v.data_to_file_field(file_data, file_content_type, '%s.pdf' % kwargs['sku'].lower().replace(' ', ''))

            if v.data.extension_publication_sample:
                # Add to sample file field
                item.pdf_sample = file_field
            else:
                # Add to download file field
                item.pdf = file_field

        # Return JSON output
        return self.getJSON(item)


# Imports Plone content as a "Learn Now Video"
class ImportVideoView(ImportProductView):

    # Adds a Video object given a context and AtlasProductImporter
    def addVideo(self, context, v, **kwargs):

        # Log message
        self.log("Creating Learn Now Video %s" % v.data.title)

        # Create video
        return self.createProduct(context, 'atlas_video', v, **kwargs)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Additional fields
        kwargs = {}

        # If the video has body text, extract the video, and add the rest as
        # the 'text' field.  This raises lots of exceptions if it doesn't find
        # exactly what it's looking for.
        if v.data.html:

            soup = BeautifulSoup(v.data.html)

            video_embeds = soup.findAll(['embed', 'iframe', 'object'])

            if not video_embeds:
                raise Exception('No video found in HTML')

            if len(video_embeds) > 1:
                raise Exception('Multiple videos found in HTML')

            video = video_embeds[0].extract()

            if video.name not in ['iframe',]:
                raise Exception('Video is not in an iframe')

            url = video.get('src', None)

            if not url:
                raise Exception('iframe does not have src attribute')

            key = None

            for regex in video_regexes:
                m = regex.match(url)
                if m:
                    key = m.group(1)

            if not key:
                raise Exception('YouTube key not found')

            if key.lower() == 'videoseries':
                raise Exception('Not a video URL %s' % url)

            kwargs['video_url'] = 'https://www.youtube.com/watch?v=%s' % key

            # Add a video
            item = self.addVideo(self.import_path, v, **kwargs)

            # Add the remaining HTML
            item.text = RichTextValue(raw=repr(soup),
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')
        else:
            raise Exception('No HTML found to extract video')

        # Return JSON output
        return self.getJSON(item)

class ImportWorkshopGroupView(ImportProductView):

    # Adds a Workshop Group object given a context and AtlasProductImporter
    def addWorkshopGroup(self, context, v, **kwargs):

        # Log message
        self.log("Creating Workshop Group %s" % v.data.title)

        # Create Workshop Group
        item = self.createProduct(context, 'atlas_workshop_group', v, **kwargs)###

        # Add the body text if it exists
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        return item

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Additional fields
        kwargs = {}

        # Add a Workshop Group
        item = self.addWorkshopGroup(self.import_path, v, **kwargs)

        # If the Workshop Group has body text, add it as the 'text' field.
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        # Return JSON output
        return self.getJSON(item)

###
class ImportWorkshopView(ImportWorkshopGroupView):

    parent_type = 'Workshop Group'

    # Find a parent group product with the same type and title as the workshop
    def getWorkshopGroup(self, title=None):

        # If we have a title for comparison, check
        if title:

            # Catalog query by type, no title (Unicode string matching issues)
            results = self.portal_catalog.searchResults({'Type' : self.parent_type})

            # Filter by title
            results = [x for x in results if safe_unicode(x.Title) == safe_unicode(title)]

            if results:
                return results[0].getObject()

        return None

    # Adds a Workshop object given a context and AtlasProductImporter
    def addWorkshop(self, context, v, **kwargs):

        # Log message
        self.log("Creating Workshop %s" % v.data.title)

        # Create Workshop
        return self.createProduct(context, 'atlas_workshop', v, **kwargs)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Additional fields
        kwargs = {}

        # Check for existing Workshop Group
        workshop_group = self.getWorkshopGroup(v.data.title)

        # If we found a Workshop Group, append this workshop's original Plone id
        # to it.
        if workshop_group:

            original_plone_ids = list(getattr(workshop_group, 'original_plone_ids', []))

            if v.data.uid not in original_plone_ids:
                original_plone_ids.append(v.data.uid)
                workshop_group.original_plone_ids = original_plone_ids
                workshop_group.reindexObject()

        # Add a Workshop Group if there isn't one
        else:
            workshop_group = self.addWorkshopGroup(self.import_path, v, **kwargs)

        # Get the location data from Google Maps integration
        location = v.data.location

        # Only attempt to look up location data if a location is provided.
        if location:

            # Use the LocationAdapter directly rather than ILocationMarker,
            # since the workshop is not created yet.
            adapted = LocationAdapter(None)
            geocode_data = adapted.geocode(location)

            # If the address lookup succeeded
            if geocode_data:

                # Get the venue, street_address, city, state, zip_code
                kwargs.update(adapted.get_address_fields(geocode_data))

                # Lat/LNG coordinates if they exist
                (lat, lng) = adapted.lookup_coords(geocode_data)

                if lat and lng:
                    kwargs['latitude'] = lat
                    kwargs['longitude'] = lng

            # Otherwise, push the provided location into the street_address field
            else:
                kwargs['street_address'] = location

        # Add the Workshop
        workshop = self.addWorkshop(workshop_group, v,
                                  **kwargs)

        # Get the workshop start/end dates
        workshop_start_date = v.data.start
        workshop_start_date = DateTime(workshop_start_date).asdatetime()

        workshop_end_date = v.data.end
        workshop_end_date = DateTime(workshop_end_date).asdatetime()

        acc = IEventAccessor(workshop)
        acc.edit(start=workshop_start_date, end=workshop_end_date)
        acc.update(start=workshop_start_date, end=workshop_end_date)

        # If the workshop recording has body text, add it as the 'text' field in
        # both the workshop and the workshop group.
        if v.data.html:
            workshop.text = RichTextValue(raw=v.data.html,
                                            mimeType=u'text/html',
                                            outputMimeType='text/x-html-safe')



        # Return JSON output
        return self.getJSON(workshop_group)



class ImportSmartSheetView(ImportProductView):

    # Adds a Smart Sheet object given a context and AtlasProductImporter
    def addSmartSheet(self, context, v, **kwargs):

        # Log message
        self.log("Creating Smart Sheet %s" % v.data.title)

        # Create Smart Sheet
        return self.createProduct(context, 'atlas_smart_sheet', v, **kwargs)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Additional fields
        kwargs = {}

        # Add a Smart Sheet
        item = self.addSmartSheet(self.import_path, v, **kwargs)

        # If this object is a file, add the file as a content object.
        if v.data.type in ('File',):
            self.addFile(item, v)

        # If we're a multi-file smartsheet, go through the contents
        for i in v.data.contents:

            # Get the importer object based on the UID
            _v = AtlasProductImporter(uid=i, domain=self.domain)

            # If we have a review state, ensure that it's Atlas Ready
            # If not, skip the import for that object
            review_state = _v.data.review_state

            if review_state and review_state not in ['atlas-ready']:
                continue

            # Based on the type, do the required import
            if _v.data.type in ('Image',):
                self.addImage(item, _v)

            elif _v.data.type in ('File',):
                self.addFile(item, _v)

        # If the Smart Sheet has body text, add it as the 'text' field.
        if v.data.html:
            item.text = RichTextValue(raw=v.data.html,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        # Return JSON output
        return self.getJSON(item)

class ImportWebinarRecordingView(ImportProductView):

    # Adds a Webinar Group object given a context and AtlasProductImporter
    def addWebinarGroup(self, context, v, **kwargs):

        # Log message
        self.log("Creating Webinar Group %s" % v.data.title)

        # Create Webinar Group
        return self.createProduct(context, 'atlas_webinar_group', v, **kwargs)

    # Adds a Webinar object given a context and AtlasProductImporter
    def addWebinar(self, context, v, **kwargs):

        # Log message
        self.log("Creating Webinar %s" % v.data.title)

        # Create Webinar
        return self.createProduct(context, 'atlas_webinar', v, **kwargs)

    # Adds a Webinar Recording object given a context and AtlasProductImporter
    def addWebinarRecording(self, context, v, **kwargs):

        # Log message
        self.log("Creating Webinar Recording %s" % v.data.title)

        return createContentInContainer(
                    context,
                    'atlas_webinar_recording',
                    id=self.getId(v),
                    title=v.data.title,
                    **kwargs)

    # Adds a Webinar File (Presentation) object given a context and AtlasProductImporter
    def addWebinarPresentation(self, context, v, **kwargs):

        # Create Webinar Presentation
        return self.addFile(context, v, portal_type='atlas_webinar_file',
                            file_type='Presentation',
                            **kwargs)

    # Adds a Webinar File (Handout) object given a context and AtlasProductImporter
    def addWebinarHandout(self, context, v, **kwargs):

        # Log message
        self.log("Creating Webinar Handout %s" % v.data.title)

        # Create Webinar Handout
        return self.addFile(context, v, portal_type='atlas_webinar_file',
                            file_type='Handout',
                            **kwargs)

    # Performs the import of content by creating an AtlasProductImporter object
    # and using that data to create the content.
    def importContent(self):

        # Create new content importer object
        v = AtlasProductImporter(uid=self.uid, domain=self.domain)

        # Additional fields
        kwargs = {}

        # Add a Webinar Group
        webinar_group = self.addWebinarGroup(self.import_path, v, **kwargs)

        # Add the Webinar
        webinar = self.addWebinar(webinar_group, v,
                                  **kwargs)

        # Set the webinar start/end dates to publish date of imported object
        webinar_date = v.data.effective
        webinar_date = DateTime(webinar_date).asdatetime()

        acc = IEventAccessor(webinar)
        acc.edit(start=webinar_date, end=webinar_date)
        acc.update(start=webinar_date, end=webinar_date)

        # Initialize webinar_url variable
        webinar_url = None

        # Add the Webinar Recording.  If we're a simple link, add the recording
        # with the link.  Otherwise, if it's a folder, cycle through the contents
        # and find links and files
        if v.data.type in ['Link',]:
            webinar_url = v.data.get_remote_url
            webinar_recording = self.addWebinarRecording(webinar, v,
                                                            webinar_recorded_url=webinar_url,
                                                            **kwargs)

        elif v.data.type in ['Folder',]:

            # Get contents data importer objects
            contents = [AtlasProductImporter(uid=x, domain=self.domain) for x in v.data.contents]

            # Get the link objects from the contents that have the webinar host in the URL
            webinar_links = [x for x in contents if x.data.type in ['Link',]]

            if webinar_links:

                # Only the first link matters
                _v = webinar_links[0]

                webinar_url = _v.data.get_remote_url

                webinar_recording = self.addWebinarRecording(webinar, v,
                                                             webinar_recorded_url=webinar_url,
                                                             **kwargs)

                # Get the files in the folder.  Assumption is that the first file is
                # the presentation, and the rest are handouts.
                webinar_files = [x for x in contents if x.data.type in ['File',]]

                webinar_presentations = webinar_files[0:1]
                webinar_handouts = webinar_files[1:]

                for _v in webinar_presentations:
                     item = self.addWebinarPresentation(webinar_recording, _v, **kwargs)

                for _v in webinar_handouts:
                     item = self.addWebinarHandout(webinar_recording, _v, **kwargs)

        # If the webinar recording has body text, add it as the 'text' field in
        # both the webinar and the webinar group.
        if v.data.html:
            webinar.text = RichTextValue(raw=v.data.html,
                                            mimeType=u'text/html',
                                            outputMimeType='text/x-html-safe')

        # If we have a 'webinar_url', set that on the Webinar Product
        if webinar_url:
            acc.edit(webinar_url=webinar_url)
            acc.update(webinar_url=webinar_url)

        # Return JSON output
        return self.getJSON(webinar_group)