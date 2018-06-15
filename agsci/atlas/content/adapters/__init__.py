from Acquisition import aq_base
from BeautifulSoup import BeautifulSoup, Tag
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import safe_unicode
from StringIO import StringIO
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from plone.app.contenttypes.interfaces import IFile, IImage
from plone.app.layout.navigation.navtree import buildFolderTree
from plone.app.textfield.value import RichTextValue
from plone.registry.interfaces import IRegistry
from urlparse import urlparse, parse_qs
from zope.component import getAdapters, getUtility
from zope.interface import Interface
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory

from agsci.api.api import BaseView as BaseAPIView
from agsci.api.api import DELETE_VALUE

from agsci.person.content.person import IPerson

from .. import IAtlasProduct
from ..behaviors import IAtlasFilterSets
from ..curriculum import ICurriculumGroup, ICurriculumInstructions, \
                         ICurriculumModule, ICurriculumLesson
from ..pdf import AutoPDF
from ..event.group import IEventGroup
from ..video import IArticleVideo
from ..vocabulary import PublicationFormatVocabularyFactory

from agsci.atlas.decorators import expensive
from agsci.atlas.interfaces import IRegistrationFieldset
from agsci.atlas.constants import DELIMITER, V_NVI, V_CS, V_C, DEFAULT_TIMEZONE, \
                                  MIMETYPE_EXTENSIONS
from agsci.atlas.counties import getSurroundingCounties
from agsci.atlas.utilities import SitePeople, ploneify

import base64
import googlemaps
import itertools
import pytz
import time
import zipfile

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

    # Traverse to the API view for the object
    @property
    def api_view(self):
        return BaseAPIView(self.context, self.context.REQUEST)

    # Get Context Review State
    def review_state(self, context=None):
        wftool = getToolByName(self.context, "portal_workflow")

        if not context:
            context = self.context

        try:
            return wftool.getInfoFor(context, 'review_state')
        except:
            return ''

    # Gets the portal_catalog object
    @property
    def portal_catalog(self):
        return getToolByName(self.context, "portal_catalog")

    # Returns the base64 encoded string of the input data
    def base64_encode(self, data):

        if data:
            return base64.b64encode(data)

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

    def isFirstPage(self, o):

        pages = self.getPageBrains()

        if pages:
            return pages[0].UID == o.UID()

        return False


# Article Adapter
class ArticleDataAdapter(ContainerDataAdapter):

    page_types = [u'Video', u'Article Page', u'Slideshow',]

    def getData(self, **kwargs):
        data = super(ArticleDataAdapter, self).getData(**kwargs)

        article_purchase = getattr(self.context, 'article_purchase', False)

        if article_purchase:
            data['publication_reference_number'] = getattr(self.context, 'publication_reference_number', None)

        # Get PDF data
        pdf_data = PDFDownload(self.context).getData(**kwargs)
        data.update(pdf_data)

        return data


# News Item Adapter
class NewsItemDataAdapter(ContainerDataAdapter):

    page_types = [u'Video', u'Slideshow',]

    def getPageCount(self):
        # Adding +1 to page_count, since the news item body text is implicitly a page
        page_count = super(NewsItemDataAdapter, self).getPageCount()
        return page_count + 1


# Video adapter
class VideoDataAdapter(BaseAtlasAdapter):

    @property
    def video_aspect_ratios(self):

        # Get the VideoAspectRatio vocabulary
        vocab_factory = getUtility(IVocabularyFactory, "agsci.atlas.VideoAspectRatio")
        vocab = vocab_factory(self.context)

        # Return vocab terms
        return [x.value for x in vocab]

    def getData(self, **kwargs):

        if self.getVideoURL():
            return {
                'video_aspect_ratio' : self.getVideoAspectRatio(),
                'video_aspect_ratio_decimal' : self.getVideoAspectRatioDecimal(),
                'video_provider' : self.getVideoProvider(),
                'video_id' : self.getVideoId(),
                'video_url' : self.getVideoURL(),
                'transcript' : self.getTranscript(),
                'video_duration_milliseconds' : self.getDuration(),
                'duration_formatted' : self.getDurationFormatted(),
            }

        return {}

    def getVideoAspectRatio(self):
        return getattr(self.context, 'video_aspect_ratio', None)

    def setVideoAspectRatio(self, v):
        if isinstance(v, (str, unicode)):
            if v in self.video_aspect_ratios:
                setattr(self.context, 'video_aspect_ratio', v)
            else:
                raise ValueError('Video aspect ratio must be a valid ratio')
        else:
            raise TypeError('Video aspect ratio must be a valid ratio, and string or unicode')

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

    def getVideoURL(self):
        return getattr(self.context, 'video_url', None)

    def getVideoId(self):

        url = self.getVideoURL()
        provider = self.getVideoProvider()

        if url and provider:

            url_object = urlparse(url)
            url_site = url_object.netloc

            # YouTube - grab the 'v' parameter

            if provider == 'YouTube':

                if url_site.endswith('youtube.com'):

                    params = parse_qs(url_object.query)

                    v = params.get('v', None)

                    if v:
                        if isinstance(v, list):
                            return v[0]
                        else:
                            return v

                elif url_site.endswith('youtu.be'):

                    # URL shortener.  Grabbing the first segment in path
                    # as the video id.  Path starts with '/', so we're
                    # ignoring the first character.
                    v = url_object.path
                    return v[1:].split('/')[0]

            # Vimeo - grab the first URl segent
            if provider == 'vimeo' or url_site.endswith('vimeo.com'):

                url_path = url_object.path

                return url_path.split('/')[1]

        return None

    def getVideoChannel(self):
        return getattr(self.context, 'video_channel_id', None)

    def setVideoChannel(self, v):

        if isinstance(v, (str, unicode)):
            setattr(self.context, 'video_channel_id', v)
        else:
            raise TypeError('Video channel must be a string or unicode')

    def getTranscript(self):
        _ = getattr(self.context, 'transcript', None)

        if isinstance(_, RichTextValue):
            return _.output

    def getDuration(self):
        return getattr(self.context, 'video_duration_milliseconds', None)

    def setDuration(self, v):

        if isinstance(v, int):
            setattr(self.context, 'video_duration_milliseconds', v)
        else:
            raise TypeError('Video duration must be an integer number of milliseconds.')

    def getDurationFormatted(self):
        v = self.getDuration()
        if v:
            seconds = v/1000.0
            # Invalid value.  Videos should never be longer than a day
            if seconds > 86400:
                return 'Invalid Time: %d seconds.'
            # One hour or more
            elif seconds >= 3600:
                return time.strftime('%H:%M:%S', time.gmtime(seconds)).lstrip('0')
            # One minute or more
            elif seconds >= 60:
                return time.strftime('%M:%S', time.gmtime(seconds)).lstrip('0')
            # Less than a minute, strip one zero
            else:
                return time.strftime('%M:%S', time.gmtime(seconds))[1:]

    @property
    def iframe_url(self):
        video_id = self.getVideoId()

        if video_id:
            return "https://www.youtube.com/embed/%s" % video_id

    @property
    def klass(self):
        k = ['youtube-video-embed']

        aspect_ratio = self.getVideoAspectRatio()

        if aspect_ratio:
            k.append('aspect-%s' % aspect_ratio.replace(':', '-'))

        return " ".join(k)


# Optional Video adapter
class OptionalVideoDataAdapter(VideoDataAdapter):

    def getData(self, **kwargs):

        if self.getVideoURL():
            return {
                'video_aspect_ratio' : self.getVideoAspectRatio(),
                'video_aspect_ratio_decimal' : self.getVideoAspectRatioDecimal(),
                'video_provider' : self.getVideoProvider(),
                'video_id' : self.getVideoId(),
                'video_url' : self.getVideoURL(),
            }

        return {}


# PDF download
class PDFDownload(BaseAtlasAdapter):

    def getData(self, **kwargs):

        # Only return data if we're getting binary data
        if kwargs.get('bin', False):

            # Grab PDF binary data and filename.
            (pdf_data, pdf_filename) = self.getPDF()

            if pdf_data:

                return {
                            'pdf_sample' : {
                                'data' : self.base64_encode(pdf_data),
                                'filename' : pdf_filename
                            },
                            'pdf' : DELETE_VALUE,
                }

        return {}

    # Attached PDF
    @property
    def pdf_file(self):
        return getattr(self.context, 'pdf_file', None)

    # Autogenerated PDF
    @property
    def pdf_autogenerate(self):
        return getattr(self.context, 'pdf_autogenerate', None)

    # Check for a PDF download or a
    def hasPDF(self):
        return self.pdf_file or self.pdf_autogenerate

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

        data = {}

        # Set page count
        page_count = self.getPageCount()

        if page_count:
            data['pages_count'] = page_count

        # Check if group product based on `publication formats` field
        publication_formats = getattr(self.context, 'publication_formats', [])

        # If we have alternate formats, the main publication is a Publication Group
        if publication_formats:
            data['plone_product_type'] = 'Publication Group'

            # If we do not have a 'bundle_publication_sku' attribute, delete
            # the price. Otherwise, this will be used as the bundle price.
            bundle_publication_sku = getattr(self.context, 'bundle_publication_sku', None)

            if not bundle_publication_sku:
                data['price'] = DELETE_VALUE

        # Otherwise, it's assumed to be Publication Print
        else:
            data['plone_product_type'] = 'Publication Print'

        # Hide the PDF field
        data['pdf'] = DELETE_VALUE

        data.update(self.api_view.mapProductType(data))

        return data

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
            'extension_structure' : self.getParentEPAS(),
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
            return V_NVI

        return V_CS

    # Gets the parent object's EPAS data
    def getParentEPAS(self):

        parent = self.getParent()

        if parent:
            parent_api_view = BaseAtlasAdapter(parent).api_view
            data = parent_api_view.getData()
            return data.get('extension_structure', [])


# Parent adapter class for events
class EventDataAdapter(BaseChildProductDataAdapter):

    parent_provider = IEventGroup

    def getHumanWhenTime(self):

        # Check for custom field
        custom_when = getattr(self.context, 'event_when_custom', [])

        if custom_when:
            try:
                if custom_when[0].strip():
                    return custom_when
            except:
                pass # Catch empty/bogus custom fields

        toLocalizedTime = self.context.restrictedTraverse('@@plone').toLocalizedTime

        # Otherwise, return a date range as a list.
        try:
            return [toLocalizedTime(self.context.start, long_format=True, end_time=self.context.end)]
        except:
            return []

    def getData(self, **kwargs):

        # Get the default child product data
        data = super(EventDataAdapter, self).getData(**kwargs)

        # Delete any "short description" and "description" values, as individual events don't have this.
        data['description'] = DELETE_VALUE
        data['short_description'] = DELETE_VALUE

        # Event-specific fields
        data['available_to_public'] = self.isAvailableToPublic()
        data['youth_event'] = self.isYouthEvent()
        data['event_walkin'] = self.walkinsAccepted()

        # When Field
        when = self.getHumanWhenTime()

        if when:
            data['event_when'] = when

        # Remove 'event_when_custom', since that's internal.
        data['event_when_custom'] = DELETE_VALUE

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

    # Returns the Bool value of 'walkin'
    # Same reason as above.
    def walkinsAccepted(self):
        return getattr(self.context, 'walkin', False)


# Adapter for Workshop/etc. groups
class EventGroupDataAdapter(ContainerDataAdapter):

    page_types = ['Workshop', 'Webinar', 'Cvent Event', 'Conference', 'External Event']

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


# Adds the counties in which the child events occur, plus all the surrounding
# counties to an event group.
class EventGroupCountyDataAdapter(EventGroupDataAdapter):

    # Aggregate counties for child events
    @property
    def counties(self):

        # List of counties to return
        rv = []

        # Get the current time, localized to the timezone.
        tz = pytz.timezone(DEFAULT_TIMEZONE)
        now = tz.localize(datetime.now())

        # Iterate through child events
        for o in self.getPages():

            # Skip if anything except published or expiring soon
            review_state = self.review_state(o)

            if review_state not in ['published', 'expiring_soon']:
                continue

            # Check to see if they're still active
            if o.end > now:

                # Get the county field
                county = getattr(o, 'county', [])

                # if it exists, and it's a valid data type
                if county and isinstance(county, (tuple, list)):

                    # Iterate through it (should only be one, but hey!)
                    for i in county:

                        # Push the surrounding counties (hardcoded in
                        # agsci.atlas.counties) onto the rv
                        rv.extend(getSurroundingCounties(i))

        # Unique the list
        rv = list(set(rv))

        # Sort the list
        rv.sort()

        # Return
        return rv

    def getData(self, **kwargs):

        # Get surrounding counties for child events

        return {
            'county' : self.counties,
        }


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

        # Get data from the parent adapter
        data = super(EventDataAdapter, self).getData(**kwargs)

        # If a webinar recording object exists, attach its fields
        data.update(self.getWebinarRecordingData())

        # Return the data
        return data


# Webinar recording data
class WebinarRecordingDataAdapter(ContainerDataAdapter):

    page_types = ['Webinar Presentation/Handout',]

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

        # Update with catalog and schema data from the API view
        data.update(
            self.api_view.getCatalogData()
        )

        data.update(
            self.api_view.getSchemaData()
        )

        # Remove unneeded fields
        exclude_fields = [
                            'event_start_date', 'event_end_date', 'description',
                            'publish_date', 'file_type', 'plone_product_type',
                        ]

        # Set product type as either Presentation or Handout. Default to 'Presentation'
        file_type = getattr(self.context, 'file_type', 'Presentation')

        if file_type:
            data['product_type'] = 'Webinar %s' % file_type

        # Filter Sets
        exclude_fields.extend([self.api_view.rename_key(x) for x in IAtlasFilterSets.names()])

        for i in exclude_fields:
            if data.has_key(i):
                del data[i]

        return data


# Gets the configured registration fields based on fieldsets selected at the
# Group level
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


# Adapter for Online Courses
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

        # Set the length_content_access to the parent's value for that field.
        parent = self.getParent()

        length_content_access = getattr(parent, 'length_content_access', None)

        if length_content_access:
            data['length_content_access'] = length_content_access

        return data


# Adapter for Apps
class ApplicationDataAdapter(ContainerDataAdapter):
    page_types = [u'Video', u'Article Page', u'Slideshow',]


# Adapter for Smart Sheets
class SmartSheetDataAdapter(ContainerDataAdapter):
    page_types = [u'File',]


# Adapter for Online Course Groups
class OnlineCourseGroupDataAdapter(ContainerDataAdapter):

    page_types = ['Online Course']

    def getData(self, **kwargs):

        data = super(OnlineCourseGroupDataAdapter, self).getData(**kwargs)

        data['sections'] = getattr(self.context, 'sections', None)

        return data


# Adapter for Curriculum Groups
class CurriculumGroupDataAdapter(ContainerDataAdapter):

    page_types = ['Curriculum (Simple)', 'Curriculum (Digital)']

    def getData(self, **kwargs):

        # Delete contents for curriculum group
        return {'contents' : DELETE_VALUE,}


# Adapter for Curriculums
class CurriculumDataAdapter(BaseChildProductDataAdapter):

    page_types = ['Curriculum Instructions', 'Curriculum Module', 'Curriculum Lesson']

    parent_provider = ICurriculumGroup

    # Filename for ZIP file, either Title and SKU or just Title
    @property
    def zip_file_filename(self):

        title = ploneify(self.context.Title(), filename=True)
        sku = getattr(self.context, 'sku', None)

        if sku:
            return u'%s_%s.zip' % (sku, title)

        return u'%s.zip' % title

    # Returns a list of files/videos, sorted by the order in which they appear.
    @property
    def files(self):
        return CurriculumContentsAdapter(self.context).getContents()

    # Gets the normalized and serialized filename for the file
    def filename(self, o):

        f = BinaryNameDataAdapter(o).normalized_filename

        if not f:
            f = o.file.filename

        return f

    # Returns the data for a file (either File or a Video) given the object
    def get_file_data(self, o):

        if o.Type() in ['File',]:
            return o.file.data

        elif o.Type() in ['Video',]:
            try:
                v = o.restrictedTraverse('@@video_embed')
            except AttributeError:
                pass
            else:
                html = v()
                return html.encode('utf-8')

    # Rreturns a list of tuples containing the UID, serialized filename, and data
    @property
    def file_data(self):

        for o in self.files:
            if IFile.providedBy(o) or IImage.providedBy(o):
                yield (o.UID(), self.filename(o), self.get_file_data(o))

    # Returns a "UID to Filename" lookup dict
    @property
    def filename_lookup(self):
        _ = {}

        for (_uid, _filename, _data) in self.file_data:
            _[_uid] = _filename

        return _

    @property
    def index(self):
        _ = self.context.restrictedTraverse('@@outline')
        return _()

    # Creates a ZIP file of the files inside the curriculum
    @property
    def zip_file(self):

        zip_data = StringIO()

        zf = zipfile.ZipFile(zip_data, "a", zipfile.ZIP_DEFLATED, False)

        # Write the index
        zf.writestr('index.html', self.index)

        for (_uid, _filename, _data) in self.file_data:
            # Write the file to the in-memory zip
            zf.writestr(_filename, _data)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0

        zf.close()

        # Return binary zip file data
        return zip_data.getvalue()

    # Returns a data structure containing the 'navigation' generated for the
    # curriculum
    @property
    def navtree(self):
        path = "/".join(self.context.getPhysicalPath())

        query = {
            'object_provides' : [
                'plone.app.contenttypes.interfaces.IFile',
                'agsci.atlas.content.video.IArticleVideo',
                'agsci.atlas.content.curriculum.ICurriculumInstructions',
                'agsci.atlas.content.curriculum.ICurriculumModule',
                'agsci.atlas.content.curriculum.ICurriculumLesson',
            ],
            'path' : path,
            'sort_on' : 'getObjPositionInParent'
        }

        return buildFolderTree(
            self.context,
            obj=self.context,
            query=query,
        )

    # Returns an HTML value for the outline of the curriculum
    def getHTML(self, standalone=False):

        soup = BeautifulSoup()

        for _ in self.build_description(self.navtree, standalone=standalone):
            soup.append(_)

        return soup.prettify()

    # Gets the YouTube URL for the video
    def getVideoURL(self, r):

        _ = VideoDataAdapter(r.getObject())
        video_id = _.getVideoId()

        if video_id:
            return u'https://www.youtube.com/watch?v=%s' % video_id

        return ''

    # Generates each piece of the outline from the navtree data
    def build_description(self, navtree, standalone=False):

        if standalone:
            filename_lookup = self.filename_lookup

        soup = BeautifulSoup()

        _ = []
        files = []

        for i in navtree.get('children', []):
            depth = i.get('depth', 1)
            r = i.get('item')

            if r.Type in ['File', 'Video']:
                _li = Tag(soup, 'li')
                _a = Tag(soup, 'a')

                if r.Type in ['Video',]:

                    # YouTube video URL
                    _a['href'] = self.getVideoURL(r)

                else:
                    file_url = 'resolveuid/%s' % r.UID

                    if standalone:
                        file_url = filename_lookup.get(r.UID, '')

                    _a['href'] = file_url

                _a.append(r.Title)
                _li.append(_a)
                _li.append(Tag(soup, 'br'))
                _li.append(r.Description)
                files.append(_li)

            else:
                tag = Tag(soup, 'h%d' % (depth+1))
                tag.append(r.Title)
                _.append(tag)

            _.extend(self.build_description(i, standalone=standalone))

        if files:
            _ul = Tag(soup, 'ul')
            for _li in files:
                _ul.append(_li)
            _.append(_ul)

        return _

    @expensive
    def getData(self, **kwargs):
        # Get the default child product data
        data = super(CurriculumDataAdapter, self).getData(**kwargs)

        # Get the HTML-ified description of the contents
        data['html'] = self.getHTML()

        # Add zip file for full curriculum if we're including binary data
        if kwargs.get('bin', False):
            data['zip_file'] = {
                'data' : self.base64_encode(self.zip_file),
                'mimetype' : 'application/zip',
            }

        # Return data
        return data


# Curriculum Content
class CurriculumContentDataAdapter(ContainerDataAdapter):

    page_types = ['Curriculum Lesson', 'File', 'Video']


# County
class CountyDataAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        county = getattr(self.context, 'county', [])

        if county and isinstance(county, (list, tuple)):
            county = county[0].lower()

        return {
            'visibility' : V_C,
            'county_4h_url' : '//extension.psu.edu/programs/4-h/counties/%s' % county,
            'county_master_gardener_url' : '//extension.psu.edu/programs/master-gardener/counties/%s' % county,
            'county_other_url' : '//extension.psu.edu/extension-directory/%s-county' % county,
        }


# Person
class PersonDataAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        # Defaults
        data = {
            'visibility' : V_C,
        }

        # Grab the Plone review_state
        review_state = self.review_state()

        # If the review_state is inactive, set plone_status to 'published', but
        # set the visibility to Not Visible Individually
        if review_state in ['published-inactive',]:
            data['plone_status'] = 'published'
            data['visibility'] = V_NVI

        # If the review_state is expired, set the visibility to Not Visible Individually
        elif review_state in ['expired',]:
            data['visibility'] = V_NVI

        # LDAP API URLs
        data['ldap_api_url_json'] = '%s/@@ldap/json' % self.context.absolute_url()
        data['ldap_api_url_xml'] = '%s/@@ldap/xml' % self.context.absolute_url()

        return data


# Shadow Product Adapter
class BaseShadowProductAdapter(BaseAtlasAdapter):

    visibility = V_NVI

    def getData(self, **kwargs):

        # Get the output of the parent class getData() method
        data = super(BaseShadowProductAdapter, self).getData(**kwargs)

        # Update the existing data dict with the @@api output.
        # Don't get subproducts
        data.update(self.api_view.getData(subproduct=False))

        # Set the 'is_sub_product' value, so we know it's a shadow product
        data["is_sub_product"] = True

        # Set the visiblity
        data['visibility'] = self.visibility

        # Remove the Magento URL from shadow products
        if data.has_key('magento_url'):
            del data['magento_url']

        # Return the data structure
        return data


# Sub Product Adapter
class BaseSubProductAdapter(BaseShadowProductAdapter):
    pass


# Shadow Article Product Adapter
class ShadowArticleAdapter(BaseShadowProductAdapter):

    @property
    def website_ids(self):

        # Get the StoreViewId vocabulary
        vocab_factory = getUtility(IVocabularyFactory, "agsci.atlas.StoreViewId")
        vocab = vocab_factory(self.context)

        # Return vocab terms
        return [x.value for x in vocab]

    def getData(self, **kwargs):

        # If it has the `article_purchase` field set, we also have a
        # for-sale publication associated with the article.
        article_purchase = getattr(self.context, 'article_purchase', False)

        if article_purchase:

            # Get the output of the parent class getData() method
            data = super(ShadowArticleAdapter, self).getData(**kwargs)

            # Get the SKU for this publication
            publication_reference_number = data.get('publication_reference_number', None)

            if publication_reference_number:

                # Update SKU and delete publication_reference_number
                data['sku'] = publication_reference_number
                del data['publication_reference_number']

                # Reset plone product type, and re-map
                data['plone_product_type'] = 'Publication Print'
                data.update(self.api_view.mapProductType(data))

                # Update the price
                data['price'] = getattr(self.context, 'price', None)

                # Update the plone_id by appending '_hardcopy'
                data['plone_id'] = '%s_hardcopy' % self.context.UID()

                # Set the store id (`website_ids`) to all valid store ids
                data['website_ids'] = self.website_ids

                # Fix data types (specifically, the price.)
                data = self.api_view.fix_value_datatypes(data)

                return data

        return {}


# Publication Subproduct Adapter
class PublicationSubProductAdapter(BaseSubProductAdapter):

    format = None
    original_product_type = 'Publication'

    @property
    def format_name(self):
        return self.formats.get(self.format, None)

    def product_name(self, data):
        return '%s (%s)' % (data['name'], self.format_name)

    @property
    def formats(self):
        vocab = PublicationFormatVocabularyFactory(self.context)
        return dict([(x.value, x.title) for x in vocab._terms])

    def getSubProductType(self, data):

        product_type_format = {
            'hardcopy' : 'Print',
            'digital' : 'Digital',
        }.get(self.format, None)

        if product_type_format:
            return '%s %s' % (self.original_product_type, product_type_format)

        return self.original_product_type

    def getData(self, **kwargs):

        # Get all alternate publication formats
        publication_formats = getattr(self.context, 'publication_formats', [])

        # Get publication format matching this format
        try:
            publication_formats = [x for x in publication_formats if x.get('format', None) == self.format]
        except TypeError:
            publication_formats = []

        # If we have a matching format entry
        if publication_formats:

            # Grab the first matching format entry
            publication_format_data = publication_formats[0]

            # This returns a copy of the publication product for an
            # alternative format.

            if self.format_name:
                # Get the output of the parent class getData() method
                data = super(PublicationSubProductAdapter, self).getData(**kwargs)

                # Set product name
                data['name'] = self.product_name(data)

                # Set 'parent_id' and 'plone_id'
                data['parent_id'] = data['plone_id']
                data['plone_id'] = '%s_%s' % (data['plone_id'], self.format)

                # Set SKU
                data['sku'] = publication_format_data.get('sku', data.get('sku', ''))

                # Set Price
                data['price'] = publication_format_data.get('price', data.get('price', ''))

                # Reset product types, and remap
                data['plone_product_type'] = self.getSubProductType(data)
                data.update(self.api_view.mapProductType(data))

                # Remove the PDF Sample
                if data.has_key('pdf_sample'):
                    del data['pdf_sample']

                # Remove bundle_publication_sku
                if data.has_key('bundle_publication_sku'):
                    del data['bundle_publication_sku']

                # If we're the digital version, add the PDF field back (if it exists)
                if self.format in ('digital'):
                    pdf_file = getattr(self.context, 'pdf', None)

                    if pdf_file and hasattr(pdf_file, 'data') and pdf_file.data:
                        data['pdf'] = pdf_file

                # Fix data types (specifically, the price.)
                data = self.api_view.fix_value_datatypes(data)

                return data

        return {}


# Adapter for hardcopy of publication
class PublicationHardCopyAdapter(PublicationSubProductAdapter):
    format = 'hardcopy'


# Adapter for digital copy of publication
class PublicationDigitalAdapter(PublicationSubProductAdapter):
    format = 'digital'


# This takes a Plone object, and returns various lat/lng related data
class LocationAdapter(object):

    def __init__(self, context):
        self.context = context

    @property
    def latitude(self):
        return getattr(self.context, 'latitude', None)

    @property
    def longitude(self):
        return getattr(self.context, 'longitude', None)

    @property
    def coords(self):
        return (self.latitude, self.longitude)

    @property
    def has_coords(self):
        return not (isinstance(self.latitude, type(None)) or isinstance(self.longitude, type(None)))

    @property
    def has_valid_coords(self):

        if self.has_coords:
            return not (self.latitude == 0 or self.longitude == 0)

        return False

    def set_coords(self, *coords):
        (lat, lng) = coords

        if lat and lng and isinstance(lat, Decimal) and isinstance(lng, Decimal):
            setattr(self.context, 'latitude', lat)
            setattr(self.context, 'longitude', lng)

            self.context.reindexObject()

    # Get the full address of the location.  Ends up as comma-joined string
    # using all the fields found.
    @property
    def full_address(self):

        # Street address
        address = getattr(self.context, 'street_address', '')

        if address and isinstance(address, (list, tuple)):
            address = [x.strip() for x in address if x.strip()]
            address = ", ".join(address)
        else:
            address = ''

        # City, State, ZIP Code
        (city, state, zip_code) = [
                                    getattr(self.context, x, '') for x in
                                    ('city', 'state', 'zip_code')
                                    ]

        # Sanity check: If we don't have a city and state, return None.  That's
        # the minimum requirement to get lat/lon
        if not city and state:
            return None

        # Full address
        full_address = [x for x in (address, city, state) if x]
        full_address = [x.strip() for x in full_address if x.strip()]

        # Return comma-joined string plus zip_code
        rv = ", ".join(full_address)

        if zip_code:
            rv = rv + " " + zip_code

        return rv

    # client() returns a Google Maps API Client
    @property
    def client(self):
        # Get the API key from the registry
        google_api_key = self.api_key

        # If we have an API key, return a client
        if google_api_key:
            return googlemaps.Client(google_api_key)

    # geocode() is its own method so we can use it elsewhere
    def geocode(self, full_address=None):

        if full_address:
            client = self.client

            if client:
                return client.geocode(full_address)

        return []

    # From geocode data(if provided) pull the address fields
    def get_address_fields(self, geocode_data=[]):

        # Return data initialization
        data = {
            'venue' : '',
            'street_address' : [],
            'city' : '',
            'state' : '',
            'zip_code' : '',
            'county' : [],
        }

        # If we aren't passed geocode_data, look it up based on the object's current address
        if not geocode_data:

            # Geocode the object's address
            geocode_data = self.geocode(self.full_address)

        for r in geocode_data:
            address_components = r.get('address_components', [])

            for c in address_components:
                types = c.get('types', [])

                # Venue
                if any([x in types for x in ['establishment', 'point_of_interest']]):
                    data['venue'] = c.get('long_name', '')

                # ZIP Code
                if any([x in types for x in ['postal_code']]):
                    data['zip_code'] = c.get('long_name', '')

                # City
                if all([x in types for x in ['locality', 'political']]):
                    data['city'] = c.get('long_name', '')

                # State
                if all([x in types for x in ['administrative_area_level_1', 'political']]):
                    data['state'] = c.get('short_name', '')

                # County
                if all([x in types for x in ['administrative_area_level_2', 'political']]):
                    county = c.get('long_name', '')

                    if county:
                        # Remove the explicit "County"
                        county = county.replace(' County', '')
                        data['county'] = [county,] # It's a list in the schema

            # Street Address
            formatted_address = [x.strip() for x in r.get('formatted_address', '').split(',')]

            # Get Start and End indexes based on venue and city
            start_idx = 0
            end_idx = -1

            venue = data.get('venue', '')
            city = data.get('city', '')

            if venue:
                if venue in formatted_address:
                    start_idx = formatted_address.index(venue) + 1

            if city:
                if city in formatted_address:
                    end_idx = formatted_address.index(city)

            # Slice the list to include just the street address line(s)
            formatted_address = formatted_address[start_idx:end_idx]

            # If we have anything left, comma join it and call it the street
            # address
            if formatted_address:
                data['street_address'] = formatted_address

        return data

    # Given an object that implements IAtlasLocation, do a Google Maps API lookup
    # based on the address.  If no lat/lon is found, return (0,0)
    def lookup_coords(self, geocode_data=[]):

        # If we aren't passed geocode_data, look it up based on the object's current address
        if not geocode_data:

            # Geocode the object's address
            geocode_data = self.geocode(self.full_address)

        # Iterate through geocode_data (if any) and return the first match for
        # lat and lng
        for r in geocode_data:
            location = r.get('geometry', {}).get('location', {})
            lat = location.get('lat', '')
            lng = location.get('lng', '')
            if lat and lng:

                # Decimal to 8 places
                lat = Decimal(lat).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)
                lng = Decimal(lng).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)

                return (lat, lng)

        return (0.0, 0.0)

    # Checks the event (lifecycle) to see if address attributes were updated
    def is_address_updated(self, event=None):
        if isinstance(event, ObjectModifiedEvent):

            address_fields = ['street_address', 'city', 'state', 'zip_code']

            # Put all of the  modified attributes into one list, and then split
            # on '.', returning the last item from the split result.
            modified_fields = [x.split('.')[-1] for x in itertools.chain(*[x.attributes for x in event.descriptions])]

            return not not set(address_fields) & set(modified_fields)

        return False

    @property
    def api_key(self):
        registry = getUtility(IRegistry)
        return registry.get('agsci.atlas.google_maps_api_key')


# Handles registration data
class EventRegistrationAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        # If the capacity for the event is set, then we *are* managing stock
        # so this returns true.  If it's not set, we *are not* managing stock.
        capacity = getattr(self.context, 'capacity', None)

        return {
            'manage_stock' : isinstance(capacity, int),
        }


# Provides a formatted duration for event groups.  If the custom value is present,
# it uses that instead.
class EventGroupDurationAdapter(BaseAtlasAdapter):

    @property
    def duration_hours(self):
        return getattr(self.context, 'duration_hours', None)

    @property
    def duration_hours_custom(self):
        return getattr(self.context, 'duration_hours_custom', None)

    # Get a human formatted duration (X hours, y minutes)
    @property
    def duration_formatted(self):

        def fmt(unit, value):
            if value:
                if value > 1:
                    return '%d %ss' % (value, unit)
                return '%d %s' % (value, unit)

        if self.duration_hours_custom:
            return self.duration_hours_custom

        elif self.duration_hours:

            (hours, minutes) = [int(x) for x in divmod(60*self.duration_hours, 60)]

            v = [fmt('hour', hours), fmt('minute', minutes)]

            return ', '.join([x for x in v if x])

    def getData(self, **kwargs):
        return {'duration_formatted' : self.duration_formatted}


# Parent class for adapter for additional categories
# __call__ returns a list of tuples of (L1, L2, L3)
class AdditionalCategoriesAdapter(object):

    # Don't provide additional categories on object providing the following
    # interfaces
    excluded_interfaces = [IPerson,]

    @property
    def return_values(self):
        return not any([x.providedBy(self.context) for x in self.excluded_interfaces])

    def __init__(self, context):
        self.context = context

    def __call__(self, **kwargs):
        return []


# Adds a "See All [x]" for each the L2 in the categories
class SeeAllCategoriesAdapter(AdditionalCategoriesAdapter):

    def addSeeAll(self, categories):
        for i in categories:
            if len(i) >= 2:
                yield (i[0], i[1], u'See All %s' % i[1])

    def __call__(self, **kwargs):
        if self.return_values:
            categories = kwargs.get('categories', [])
            return list(set(self.addSeeAll(categories)))


# If the 'homepage_feature' checkbox is checked, return a category
# that indicates that this is a feature.
class HomepageFeatureCategoriesAdapter(AdditionalCategoriesAdapter):

    l2_config = {
        'Workshop Group' : 'Upcoming Workshops',
        'Article' : 'Featured Articles',
        'Online Course Group' : 'Featured Online Courses',
    }

    l1 = "Home Page Featured Blocks"

    # Featured L2 name by type.  If type not configured, return None
    @property
    def l2(self):
        return self.l2_config.get(self.context.Type(), None)

    def __call__(self, **kwargs):
        if not not getattr(self.context, 'homepage_feature', False):
            if self.l2:
                return [(self.l1, self.l2)]


# If the 'homepage_topics' are selected is checked, return a category
# that indicates the homepage topic.
class HomepageTopicsCategoriesAdapter(AdditionalCategoriesAdapter):

    l1 = "Home Page Topics"

    @property
    def homepage_topics(self):
        homepage_topics = getattr(self.context, 'homepage_topics', [])

        if homepage_topics:
            return homepage_topics

        return []

    def __call__(self, **kwargs):
        data = []

        for i in self.homepage_topics:
            data.append((self.l1, i))

        return data


# If the 'homepage_topics' are selected is checked, return a subcategory
# for each level 2 with that topic as a level 3.
class Level2HomepageTopicsCategoriesAdapter(HomepageTopicsCategoriesAdapter):

    def addL3Topic(self, categories):
        for i in categories:
            if len(i) >= 2:
                for j in self.homepage_topics:
                    yield (i[0], i[1], j)

    def __call__(self, **kwargs):
        if self.return_values:
            categories = kwargs.get('categories', [])
            return list(set(self.addL3Topic(categories)))


# If the 'educational_drivers' are selected is checked, return a category
# that indicates the educational driver(s)
class EducationalDriversCategoriesAdapter(AdditionalCategoriesAdapter):

    def __call__(self, **kwargs):
        data = []

        educational_drivers = getattr(self.context, 'atlas_educational_drivers', [])

        if educational_drivers:

            for i in educational_drivers:
                data.append(tuple(i.split(DELIMITER)))

        return data


# For people, who do not have a Level 3 category, add a fake "[L2] Experts" category for L3
class PersonCategoriesAdapter(AdditionalCategoriesAdapter):

    def __call__(self, **kwargs):
        data = []

        # Get the level 2 category from the person
        l2 = getattr(self.context, 'atlas_category_level_2', [])

        # If there are level 2 categories:
        #  * loop through them
        #  * split on delimiter
        #  * Add an L3 of "[L2] Experts" to that category
        #  * Append that tweaked category to the return list

        if l2:
            for i in l2:
                v = i.split(DELIMITER)

                if len(v) == 2:
                    v.append('%s Experts' % v[1])
                    data.append(tuple(v))

        return data


# Base class for person directory entry
class PersonDirectoryAdapterBase(AdditionalCategoriesAdapter):

    # L1 hard coded
    base = u"Penn State Extension Directory"

    # Field name
    field = ''

    # Values
    @property
    def values(self):

        v = getattr(self.context, self.field, [])

        if v and isinstance(v, (list, tuple)):
            for i in v:
                yield i

    def __call__(self, **kwargs):

        data = []

        for i in self.values:
            data.append((self.base, i))

        return data


# Present directory classifications as L1/L2 categories
class PersonClassificationsAdapter(PersonDirectoryAdapterBase):

    field = 'classifications'


# Present directory locations as L1/L2 categories
class PersonLocationAdapter(PersonDirectoryAdapterBase):

    field = 'county'

    @property
    def counties(self):
        # Get the County vocabulary
        vocab_factory = getUtility(IVocabularyFactory, "agsci.atlas.County")
        vocab = vocab_factory(self.context)

        # Return vocab terms
        return [x.value for x in vocab]

    def __call__(self, **kwargs):

        data = []

        all_counties = self.counties

        for i in self.values:

            # If we're a county, append 'County Staff Directory' to the value
            if i in all_counties:
                i = '%s County Staff Directory' % i

            data.append((self.base, i))

        return data


# Adds the 'iwd_featured_product' value for products featured on the L2 level
class CategoryL2IsFeature(BaseAtlasAdapter):

    def getData(self, **kwargs):

        return {
            'iwd_featured_product' : not not getattr(self.context, 'is_featured', False),
            'is_featured_product' : DELETE_VALUE,
        }


# Adapter for programs and hyperlinks
class ProgramHyperlinkAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        return {
            'visibility' : V_C,
        }


# Adapter for content with external authors
class ExternalAuthorsAdapter(BaseAtlasAdapter):

    former_terms = ['Former', 'Retired', 'Emeritus', 'Emerita']

    def getInactivePersonData(self, _id):
        sp = SitePeople(active=False)
        r = sp.getPersonById(_id)

        if r:
            if r.review_state in (sp.inactive_review_state,):

                job_title = None

                o = r.getObject()

                job_titles = getattr(o, 'job_titles', [])

                if job_titles and isinstance(job_titles, (list, tuple)):
                    job_title = safe_unicode(job_titles[0])

                    if not any([x.lower() in job_title.lower() for x in self.former_terms]):
                        job_title = u'Former %s' % job_title

                return {
                    'name' : r.Title,
                    'job_title' : job_title,
                    'organization' : 'Pennsylvania State University',
                    'email' : None,
                    'website' : None,
                }

    def getData(self, **kwargs):

        people_data = []

        authors = getattr(self.context, 'authors', [])

        if authors and isinstance(authors, (list, tuple)):

            inactive_people_data = [self.getInactivePersonData(x) for x in authors]

            inactive_people_data = [x for x in inactive_people_data if x]

            if inactive_people_data:
                people_data.extend(inactive_people_data)

        external_authors = getattr(self.context, 'external_authors', [])

        if external_authors:
            people_data.extend(external_authors)

        if people_data:

            return {
                'external_authors' : people_data,
            }


# Adapter for Products Hidden From Listing.  Adjusts visibility based on 'hide_product' checkbox.
class HiddenProductAdapter(BaseAtlasAdapter):

    @property
    def is_child_product(self):
        from agsci.atlas.indexer import IsChildProduct
        _ = IsChildProduct(self.context)
        return _()

    def getData(self, **kwargs):

        data = {
            'hide_product' : DELETE_VALUE
        }

        hide_product = getattr(aq_base(self.context), 'hide_product', False)

        if hide_product:

            # If we're not a child product, set the visiblity to just 'catalog'
            if not self.is_child_product:
                data['visibility'] = V_C

        return data


# For images and files, fake a 'name' based on the 'short_name' if 'name' isn't
# present.
class BinaryNameDataAdapter(BaseAtlasAdapter):

    @property
    def token(self):

        # Returns the position of the file in the parent module/lesson
        def serial(o):

            parent = o.aq_parent

            uids = [x.UID() for x in parent.listFolderContents({'Type' : o.Type()})]

            try:
                _ = uids.index(o.UID())
            except:
                _ = 0

            return _ + 1

        v = []

        for o in self.context.aq_chain:

            if ICurriculumInstructions.providedBy(o):
                v.insert(0, 'Instructions')

            if ICurriculumModule.providedBy(o):
                v.insert(0, 'Module_%02d' % serial(o))

            if ICurriculumLesson.providedBy(o):
                v.insert(0, 'Lesson_%02d' % serial(o))

            if IAtlasProduct.providedBy(o):
                break

            if IPloneSiteRoot.providedBy(o):
                break

        if v:
            return u'%s_-_' % "_".join(v)

        return ''

    # Returns the binary field
    @property
    def binary_field(self):

        # If we're a file
        if IFile.providedBy(self.context):
            return self.context.file

        # If we're an image
        if IImage.providedBy(self.context):
            return self.context.image

    # Gets the filename of the file/image
    @property
    def filename(self):

        try:
            return self.binary_field.filename
        except:
            pass

    @property
    def mimetype(self):

        try:
            return self.binary_field.contentType
        except:
            pass

    @property
    def is_video(self):
        return IArticleVideo.providedBy(self.context)

    # Gets the extension of the file by parsing the filename.  If that fails, we
    # can look it up in the mimetypes_registry
    @property
    def file_extension(self):

        # If we're a video, we'll be embedding an HTML file
        if self.is_video:
            return 'html'

        # Get the filename and mimetype
        filename = self.filename
        mimetype = self.mimetype

        # Get based on mimetype hardcoding
        if MIMETYPE_EXTENSIONS.has_key(mimetype):
            return MIMETYPE_EXTENSIONS.get(mimetype)

        # If the object has a filename associated
        if filename:

            # Grab the extension if it exists
            if '.' in filename:
                extension = filename.split('.')[-1].lower()

                # Hardcoded corrections for .jpeg extension
                return {
                    'jpeg' : 'jpg',
                }.get(extension, extension)

        return '.data'

    @property
    def normalized_title(self):

        # Start with the object title
        title = self.context.Title()

        # If the object title doesn't exist, use the short name
        if not title:

            title = self.context.getId()

            # If the short name has a '.', strip off the last segment, since
            # that's probably the file extension
            if '.' in title:
                title = ' '.join(title.split('.'))[:-1]

        # If our parent is a curriculum object, get the normalized title of the
        # Plone object in camelcase/underscore format
        p = self.context.aq_parent

        if ICurriculumInstructions.providedBy(p) or \
           ICurriculumModule.providedBy(p) or \
           ICurriculumLesson.providedBy(p):
            return '%s%s' % (self.token, ploneify(title, filename=True))

        # Get the normalized title of the Plone object
        else:
            return ploneify(title)

    # Return a filename of the normalized title concatenated with the extension
    # of the file in the file field.  If it's a curriciulm, also include the
    # token for the module/lesson
    @property
    def normalized_filename(self):

        extension = self.file_extension

        if extension:
            normalized_title = self.normalized_title
            return "%s.%s" % (normalized_title, extension)

    def getData(self, **kwargs):

        data = {}

        normalized_filename = self.normalized_filename
        normalized_title = self.normalized_title

        catalog_data = self.api_view.getCatalogData()

        name = catalog_data.get('name', None)

        if not name:
            data['name'] = normalized_title

        if normalized_title:
            data['short_name'] = normalized_title

        if normalized_filename:
            data['filename'] = normalized_filename

        return data


# Incorrect assumptions in the integration are apparently using the <magento_url>
# field that is exposed through the API.  We are fixing the glitch in an Office-spacey
# way by removing the field for all products except people.
class RemoveMagentoURL(BaseAtlasAdapter):

    def getData(self, **kwargs):

        return {
            'magento_url' : DELETE_VALUE,
        }


# The formats (iOS/Android/etc.) for Apps
class ApplicationAvailableFormatsAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        available_formats = getattr(self.context, 'available_formats', [])

        if available_formats:

            def sort_key(x):
                return x.get('title', '')

            rv = []

            for _ in available_formats:

                i = dict(_)

                if i.has_key('description'):

                    title = i.get('title', '')
                    description = i.get('description', '')

                    if title and description:
                        i['title'] = "%s %s" % (title, description.strip())

                    del i['description']

                rv.append(i)

            return {
                'available_formats' : sorted(rv, key=lambda x: sort_key(x))
            }


# Returns a structure for the updated EPAS info
class EPASAdapter(BaseAtlasAdapter):

    def getData(self, **kwargs):

        # dict to return
        data = {}

        # Prefix and key for structure
        key = 'epas'

        # Fields from Plone
        fields = ['epas_unit', 'epas_team', 'epas_topic',]

        # Replace the key_ so we're not duplicating data
        api_fields = [x.replace('%s_' % key, '') for x in fields]

        # Delete the existing values
        data = dict([(x, DELETE_VALUE) for x in fields])

        # Last field is significant.  Get that field name and value.
        f = fields[-1]

        v = getattr(self.context, f, [])

        # Iterate through the value(s) in the last field, and add them to the
        # structure
        if v:
            for i in v:

                if not data.has_key(key):
                    data[key] = []

                _ = dict(zip(api_fields, i.split(DELIMITER)))

                data[key].append(_)

        # Return what we've populated
        return data


# Lists contents (standard listing)
class ProductContentsAdapter(BaseAtlasAdapter):

    def getContents(self):
        return self.context.listFolderContents()


# Do *not* lists contents (dummy all-purpose adapter for no contents)
class NoContentsAdapter(BaseAtlasAdapter):

    def getContents(self):
        return []


# This gets just the files inside the curriculum, since the content is built dynamically.
class CurriculumContentsAdapter(ProductContentsAdapter):

    types = ['File', 'Video']

    def getContents(self):
        path = "/".join(self.context.getPhysicalPath())

        results = self.portal_catalog.searchResults({
            'Type' : self.types,
            'path' : path,
        })

        return [x.getObject() for x in results]


# Contents of a Curriculum that are Files only
class CurriculumFileContentsAdapter(CurriculumContentsAdapter):
    types = ['File',]