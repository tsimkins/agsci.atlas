from plone.app.event.browser.event_view import EventView as _EventView

from agsci.atlas.content.adapters import VideoDataAdapter, EventDataAdapter

from agsci.atlas.interfaces import IArticleMarker, INewsItemMarker, \
                                   ISlideshowMarker, \
                                   IEventGroupMarker, IAppMarker, \
                                   ISmartSheetMarker, IOnlineCourseGroupMarker

from agsci.atlas.utilities import increaseHeadingLevel

from agsci.atlas.content.event.webinar.recording import IWebinarRecording


import pytz

from .base import BaseView

from datetime import datetime

class ProductView(BaseView):

    long_date_format = '%B %d, %Y %I:%M%p'

    def getText(self, adjust_headings=False):
        if hasattr(self.context, 'text'):
            if self.context.text:
                text = self.context.text.output

                if adjust_headings:
                    return increaseHeadingLevel(text)

                return text
        return None

    def fmt(self, dt):
        return dt.strftime(self.long_date_format).replace(' 0', ' ')

    def isEvent(self, brain):
        return brain.Type in ['Workshop', 'Webinar', 'Cvent Event', 'Conference']

    def getURL(self, brain):

        if brain.Type in ['File']:
            return '%s/view' % brain.getURL()

        return brain.getURL()

    @property
    def adapted(self):
        return self.context

    def pages(self):
        return []

class ArticleView(ProductView):

    def pages(self):
        return IArticleMarker(self.context).getPageBrains()


class ArticleContentView(ProductView):
    pass


class NewsItemView(ProductView):

    def pages(self):
        return INewsItemMarker(self.context).getPageBrains()


class SlideshowView(ArticleContentView):

    def images(self):
        return ISlideshowMarker(self.context).getImages()


class VideoView(ArticleContentView):

    @property
    def adapted(self):
        return VideoDataAdapter(self.context)

    def getVideoId(self):
        return self.adapted.getVideoId()

    def getVideoProvider(self):
        return self.adapted.getVideoProvider()


class WebinarRecordingView(ProductView):

    def files(self):
        return self.context.getFolderContents({'Type' : 'Webinar Presentation/Handout'})

class EventView(_EventView, ProductView):

    def fmt(self, datestamp):

        if isinstance(datestamp, datetime):
            tz = pytz.timezone(self.context.timezone)
            localized_datetime = datestamp.astimezone(tz)
            return localized_datetime.strftime(self.long_date_format).replace(' 0', ' ')

        return 'N/A'

    def start(self):
        return self.fmt(self.context.start)

    def end(self):
        return self.fmt(self.context.end)

    @property
    def adapted(self):
        return EventDataAdapter(self.context)

    def pages(self):
        return self.adapted.getPageBrains()

class WebinarView(EventView):

    pass

class ConferenceView(EventView):

    pass

class ApplicationView(ProductView):

    def pages(self):
        return IAppMarker(self.context).getPageBrains()

class SmartSheetView(ProductView):

    def pages(self):
        return ISmartSheetMarker(self.context).getPageBrains()


class EventGroupView(ProductView):

    def pages(self):
        return IEventGroupMarker(self.context).getPageBrains()

class OnlineCourseGroupView(ProductView):

    def pages(self):
        return IOnlineCourseGroupMarker(self.context).getPageBrains()

class WorkshopGroupView(EventGroupView):
    pass

class WebinarGroupView(EventGroupView):
    pass

class CountyView(ProductView):
    pass