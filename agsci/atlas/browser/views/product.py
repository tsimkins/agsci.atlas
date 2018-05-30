from Acquisition import aq_base
from plone.app.event.browser.event_view import EventView as _EventView

from agsci.atlas.content.adapters import VideoDataAdapter, EventDataAdapter, \
                                         CurriculumDataAdapter

from agsci.atlas.interfaces import IArticleMarker, INewsItemMarker, \
                                   ISlideshowMarker, \
                                   IEventGroupMarker, IAppMarker, \
                                   ISmartSheetMarker, IOnlineCourseGroupMarker, \
                                   ICurriculumMarker

from agsci.atlas.utilities import increaseHeadingLevel

import pytz

from .base import BaseView

from datetime import datetime

class ProductView(BaseView):

    long_date_format = '%B %d, %Y %I:%M%p'

    def getText(self, adjust_headings=False):
        context = aq_base(self.context)

        if hasattr(context, 'text'):
            if context.text:
                text = context.text.output

                if adjust_headings:
                    return increaseHeadingLevel(text)

                return text
        return None

    def fmt(self, dt):
        return dt.strftime(self.long_date_format).replace(' 0', ' ')

    def isEvent(self, brain):
        return brain.Type in ['Workshop', 'Webinar', 'Cvent Event', 'Conference', 'External Event']

    def isLocationEvent(self, brain):
        return brain.Type in ['Workshop', 'Cvent Event', 'Conference',]

    def eventLocation(self, brain):
        if self.isLocationEvent(brain):
            o = brain.getObject()

            location = []

            city = getattr(o, 'city', None)
            state = getattr(o, 'state', None)

            if state and city:
                if state == 'PA':
                    location.append(city)
                else:
                    location.append("%s, %s" % (city, state))
            elif city:
                location.append(city)

            county = getattr(o, 'county', None)

            if isinstance(county, (list, tuple)) and county:
                county = ", ".join(county)
                location.append("County: %s" % county)

            if location:
                return "[%s]" % " / ".join(location)

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

    @property
    def iframe_url(self):
        return self.adapted.iframe_url

    @property
    def klass(self):
        return self.adapted.klass


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

class CurriculumGroupView(ProductView):

    def pages(self):
        return ICurriculumMarker(self.context).getPageBrains()

class CurriculumView(CurriculumGroupView):
    pass

class CurriculumDigitalView(CurriculumGroupView):

    @property
    def adapted(self):
        return CurriculumDataAdapter(self.context)

    @property
    def sku(self):
        _ = getattr(self.context, 'sku', None)

        if _:
            return _

    @property
    def title(self):
        return self.context.aq_parent.Title()

    @property
    def logo_url(self):

        url = u'https://agsci.psu.edu/assets/curriculum/extension-logo.png'

        sku = self.sku

        if sku:
            return u"%s?sku=%s" % (url, sku)

        return url

    @property
    def outline(self):
        return self.adapted.getHTML(standalone=True)

class WorkshopGroupView(EventGroupView):
    pass

class WebinarGroupView(EventGroupView):
    pass

class CountyView(ProductView):
    pass