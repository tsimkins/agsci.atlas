from datetime import timedelta
from urlparse import urlparse, parse_qs
from zope.component import getAdapters
from zope.interface import Interface
from StringIO import StringIO

from agsci.api.api import BaseView as BaseAPIView

from .pdf import AutoPDF
from .event.group import IEventGroup

from ..interfaces import IRegistrationFieldset

import base64

try:
    from pyPdf import PdfFileReader
except ImportError:
    def PdfFileReader(*args, **kwargs):
        return None

# Base class, so we always have a 'getData' method

class BaseAtlasAdapter(object):

    def __init__(self, context):
        self.context = context

    def getData(self, **kwargs):
        return {}

# Container Adapter
class ContainerDataAdapter(BaseAtlasAdapter):

    page_types = []

    def getData(self, **kwargs):

        return {

            'pages_count' : self.getPageCount(),
            'multi_page' : self.isMultiPage(),
        }

    def getPages(self):

        pages = self.context.listFolderContents({'Type' : self.page_types})

        return pages

    def getPageBrains(self):

        pages = self.context.getFolderContents({'Type' : self.page_types})

        return pages

    def getPageCount(self):
        return len(self.getPages())

    def isMultiPage(self):
        return (self.getPageCount() > 1)

# Article Adapter
class ArticleDataAdapter(ContainerDataAdapter):

    page_types = [u'Video', u'Article Page', u'Slideshow',]

# News Item Adapter
class NewsItemDataAdapter(ContainerDataAdapter):

    page_types = [u'Video', u'Slideshow',]

    def getPageCount(self):
        # Adding +1 to page_count, since the news item body text is implicitly a page
        page_count = super(NewsItemDataAdapter, self).getPageCount()
        return page_count + 1

# Video adapter
class VideoDataAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):
        return {
            'video_aspect_ratio' : self.getVideoAspectRatio(),
            'video_aspect_ratio_decimal' : self.getVideoAspectRatioDecimal(),
            'video_provider' : self.getVideoProvider(),
            'video_id' : self.getVideoId(),
            'transcript' : self.getTranscript(),
            'video_duration_milliseconds' : self.getDuration(),
            'duration_formatted' : self.getDurationFormatted(),
        }

    def getVideoAspectRatio(self):
        return getattr(self.context, 'video_aspect_ratio', None)

    def getVideoAspectRatioDecimal(self):
        v = self.getVideoAspectRatio()

        try:
            if ':' in v:
                (w,h) = [float(x) for x in v.split(':')]
                return w/h
        except:
            return None

    def getVideoProvider(self):
        return getattr(self.context, 'video_provider', None)

    def getVideoId(self):

        url = getattr(self.context, 'video_url', None)
        provider = self.getVideoProvider()

        if url and provider:

            url_object = urlparse(url)
            url_site = url_object.netloc

            # YouTube - grab the 'v' parameter

            if provider == 'youtube' or url_site.endswith('youtube.com'):

                params = parse_qs(url_object.query)

                v = params.get('v', None)

                if v:
                    if isinstance(v, list):
                        return v[0]
                    else:
                        return v

            # Vimeo - grab the first URl segent
            if provider == 'vimeo' or url_site.endswith('vimeo.com'):

                url_path = url_object.path

                return url_path.split('/')[1]

        return None

    def getVideoChannel(self):
        return getattr(self.context, 'video_channel_id', None)

    def getTranscript(self):
        return getattr(self.context, 'transcript', None)

    def getDuration(self):
        return getattr(self.context, 'video_duration_milliseconds', None)

    def getDurationFormatted(self):
        v = self.getDuration()
        if v:
            return '%s' % timedelta(milliseconds=v)

# PDF download
class PDFDownload(BaseAtlasAdapter):

    def getData(self, **kwargs):

        # Only return data if we're getting binary data
        if kwargs.get('bin', False):

            # Grab PDF binary data and filename.
            (pdf_data, pdf_filename) = self.getPDF()

            if pdf_data:

                return {
                            'pdf' : {
                                'data' : base64.b64encode(pdf_data),
                                'filename' : pdf_filename
                            }
                }

        return {}

    # Check for a PDF download or a
    def hasPDF(self):
        return getattr(self.context, 'pdf_file', None) or getattr(self.context, 'pdf_autogenerate', False)

    # Return the PDF data and filename, or (None, None)
    def getPDF(self):

        if self.hasPDF():
            # Since the filename calcuation logic is in the AutoPDF class, initialize
            # an instance, and grab the filename
            auto_pdf = AutoPDF(self.context)
            filename = auto_pdf.getFilename()

            # Check to see if we have an attached file
            pdf_file = getattr(self.context, 'pdf_file', None)

            # If we have an attached file, return that and the calculated filename
            if pdf_file:
                return (pdf_file.data, filename)

            # Otherwise, check for the autogenerate option
            elif getattr(self.context, 'pdf_autogenerate', False):
                return (auto_pdf.createPDF(), filename)

        # PDF doesn't exist or not enabled, return nothing
        return (None, None)


# Publication data
class PublicationDataAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        page_count = self.getPageCount()

        if page_count:

            return { 'pages_count' : page_count }

        return {}

    # If the page count is not manually set PDF is attached, automagically grab the page count for the API
    def getPageCount(self):

        # Get the hardcoded page count, and return if it's there
        page_count = getattr(self.context, 'pages_count', None)

        if page_count:
            return page_count

        # Otherwise, grab the page count from the attached downloadable PDF.
        # Note that this ignores the sample PDF.
        elif self.context.pdf:

            if self.context.pdf.data and self.context.pdf.contentType == 'application/pdf':
                try:
                    pdf_data = StringIO(self.context.pdf.data)
                    pdf = PdfFileReader(pdf_data)
                    return pdf.getNumPages()
                except:
                    pass

        return None

# Slideshow data
class SlideshowDataAdapter(BaseAtlasAdapter):

    def getImages(self):
        return self.context.listFolderContents({'Type' : 'Image'})

# Parent adapter class for child products
class BaseChildProductDataAdapter(ContainerDataAdapter):

    parent_provider = Interface

    def getData(self, **kwargs):

        # Basic fields
        return {
            'parent_id' : self.getParentId(),
            'visibility' : self.getVisibility(),
        }

    # Gets the parent event group for the event
    def getParent(self):

        # Get the Plone parent of the event
        parent = self.context.aq_parent

        # If our parent is an event group, return the parent
        if self.parent_provider.providedBy(parent):
            return parent

        return None

    # Returns the id of the parent event group, if it exists
    def getParentId(self):

        # Get the parent of the event
        parent = self.getParent()

        # If we have a parent
        if parent:
            # Return the Plone UID of the parent
            return parent.UID()

        return None

    # If this is part of a "group",
    def getVisibility(self):

        if self.getParent():
            return 'Not Visible Individually'

        return 'Catalog, Search'

# Parent adapter class for events
class EventDataAdapter(BaseChildProductDataAdapter):

    parent_provider = IEventGroup

    def getData(self, **kwargs):

        # Get the default child product data
        data = super(EventDataAdapter, self).getData(**kwargs)

        # Event-specific fields
        data['available_to_public'] = self.isAvailableToPublic()
        data['youth_event'] = self.isYouthEvent()

        return data

    # Returns the Bool value of 'available_to_public'
    # For some reason, this is not in the __dict__ of self.context, so we're
    # making a method to return it, and calling it directly in the API. Bool
    # weirdness?
    def isAvailableToPublic(self):
        return getattr(self.context, 'available_to_public', True)

    # Returns the Bool value of 'youth_event'
    # Same reason as above.
    def isYouthEvent(self):
        return getattr(self.context, 'youth_event', False)


class EventGroupDataAdapter(ContainerDataAdapter):

    page_types = ['Workshop', 'Webinar', 'Cvent Event', 'Conference']

    def getSortKey(self, x):
        if hasattr(x, 'start'):
            if hasattr(x.start, '__call__'):
                return x.start()
            return x.start
        return None

    def getPages(self):

        pages = super(EventGroupDataAdapter, self).getPages()

        pages.sort(key=lambda x: self.getSortKey(x))

        return pages

    def getPageBrains(self):
        pages = super(EventGroupDataAdapter, self).getPageBrains()

        pages = [x for x in pages]

        pages.sort(key=lambda x: self.getSortKey(x))

        return pages

# Webinar data
class WebinarDataAdapter(EventDataAdapter):

    page_types = ['Webinar Recording',]

    def getWebinarRecordingData(self):

        # Get the webinar recording object, and attach its field as an item
        pages = self.getPages()

        if pages:
            return WebinarRecordingDataAdapter(pages[0]).getData()

        return {}

    def getData(self, **kwargs):

        # If a webinar recording object exists, attach its fields
        return self.getWebinarRecordingData()

# Webinar recording data
class WebinarRecordingDataAdapter(ContainerDataAdapter):

    page_types = ['Webinar Presentation', 'Webinar Handout']

    def getData(self, **kwargs):

        data = {}

        link = getattr(self.context, 'webinar_recorded_url', None)

        if link:

            data['related_download_product_ids'] = [self.context.UID(), ]
            data['webinar_recorded_url'] = link

            # Add additional fields to the parent webinar.
            for k in ['duration_formatted', 'transcript', 'length_content_access', 'watch_now']:
                v = getattr(self.context, k, None)

                if v:
                    data[k] = v

            # Explicit False for watch_now
            if not data.has_key('watch_now'):
                data['watch_now'] = False

            # Now, attach the handouts and presentations
            files = self.getPages()

            if files:
                data['webinar_recorded_files'] = [ WebinarRecordingFileDataAdapter(x).getData() for x in files ]

        return data

# Webinar file data
class WebinarRecordingFileDataAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        # Initialize data dict
        data = {}

        # Grab the API view for this object
        api_view = BaseAPIView(self.context, self.context.REQUEST)

        # Update with catalog and schema data from the API view
        data.update(
            api_view.getCatalogData()
        )

        data.update(
            api_view.getSchemaData()
        )

        # Remove unneeded fields
        for i in ['event_start_date', 'event_end_date', 'description', 'publish_date',]:
            if data.has_key(i):
                del data[i]

        return data

class RegistrationFieldsetDataAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        # Check if we have a parent event group.  If so, don't return any fields
        if EventDataAdapter(self.context).getParentId():
            return {}

        # Initialize lists for data
        registration_fieldsets = []
        registration_fields = []

        # Get the fieldsets configured at the product level
        registration_fieldset_config = getattr(self.context, 'registration_fieldsets', [])

        # Iterate through the Registration Fieldsets looked up by interface
        for (name, adapted) in getAdapters((self.context,), IRegistrationFieldset):

            # If it's selected, or it's a required fieldset, append to registration_fieldsets
            if name in registration_fieldset_config or adapted.required:
                registration_fieldsets.append(adapted)

        # Sort registration_fieldsets by the sort_order key
        registration_fieldsets.sort(key=lambda x: x.sort_order)

        # Iterate through the sorted fieldsets, append the individual fields to
        # the registration_fields list
        for i in registration_fieldsets:
            registration_fields.extend(i.getFields())

        # The fields are now sorted.  However, add an explicity 'sort_order'
        # key to the field dict
        for i in range(0, len(registration_fields)):
            registration_fields[i]['sort_order'] = i

        # Return the snippet of data with the fields
        return {
            'registration_fields' : registration_fields,
            'ticket_type' : { 'title' : 'ticket type',
                              'is_require' : False,
                              'is_ticket_option' : True,
            }
        }

# Online Course
class OnlineCourseDataAdapter(BaseChildProductDataAdapter):

    def getData(self, **kwargs):

        # Get the default child product data
        data = super(OnlineCourseDataAdapter, self).getData(**kwargs)

        # Grab the explicity edX id
        edx_id = getattr(self.context, 'edx_id', None)

        # If that id exists, use it for edx_id
        if edx_id and edx_id.strip():

            data['edx_id'] = edx_id

        else:
            # Grab the SKU, and if it exists, use that for the edx_id
            sku = getattr(self.context, 'sku', None)

            if sku and sku.strip():

                data['edx_id'] = sku

        return data

# Tool/Application

class ToolApplicationDataAdapter(ContainerDataAdapter):

    page_types = [u'Video', u'Article Page', u'Slideshow',]

# Online Course Group

class OnlineCourseGroupDataAdapter(ContainerDataAdapter):

    page_types = ['Online Course']

# County
class CountyDataAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        county = getattr(self.context, 'county', '').lower()

        return {
            'county_4h_url' : '//extension.psu.edu/4-h/counties/%s' % county,
            'county_master_gardener_url' : '//extension.psu.edu/plants/master-gardener/counties/%s' % county,
        }