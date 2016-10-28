from datetime import timedelta
from urlparse import urlparse, parse_qs
from zope.component import adapter
from zope.interface import implementer

from agsci.atlas.utilities import encode_blob

from .pdf import AutoPDF
from .article import IArticle
from .news_item import INewsItem
from .behaviors import IPDFDownload

from ..interfaces import IArticleMarker, IPDFDownloadMarker, IVideoMarker, IAtlasVideoFields, INewsItemMarker

import base64

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
@adapter(IArticle)
@implementer(IArticleMarker)
class ArticleDataAdapter(ContainerDataAdapter):

    page_types = [u'Video', u'Article Page', u'Slideshow',]

# Article Adapter
@adapter(INewsItem)
@implementer(INewsItemMarker)
class NewsItemDataAdapter(ContainerDataAdapter):

    page_types = [u'Video', u'Slideshow',]
    
    def getPageCount(self):
        # Adding +1 to page_count, since the news item body text is implicitly a page
        page_count = super(NewsItemDataAdapter, self).getPageCount()
        return page_count + 1

@adapter(IAtlasVideoFields)
@implementer(IVideoMarker)
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

        url = getattr(self.context, 'video_link', None)
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

@adapter(IPDFDownload)
@implementer(IPDFDownloadMarker)
class PDFDownload(BaseAtlasAdapter):

    def getData(self, **kwargs):
    
        # If we're not getting binary data, return nothing
        if not kwargs.get('bin', False):
            return {}
    
        # Grab PDF binary data and filename.
        (pdf_data, pdf_filename) = self.getPDF()
        
        if pdf_data:

            return {
                        'pdf' : {
                            'data' : base64.b64encode(pdf_data),
                            'filename' : pdf_filename
                        }
            }

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
