from plone.app.event.browser.event_view import EventView as _EventView

from agsci.atlas.interfaces import IArticleMarker, INewsItemMarker, \
                                   ISlideshowMarker, IVideoMarker, \
                                   IWebinarMarker, IWorkshopMarker

from agsci.atlas.utilities import increaseHeadingLevel

import pytz

from .base import BaseView

from datetime import datetime

class ProductView(BaseView):

    def getText(self, adjust_headings=False):
        if hasattr(self.context, 'text'):
            if self.context.text:
                text = self.context.text.output

                if adjust_headings:
                    return increaseHeadingLevel(text)

                return text
        return None


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

    def getVideoId(self):
        return IVideoMarker(self.context).getVideoId()

    def getVideoProvider(self):
        return IVideoMarker(self.context).getVideoProvider()


class WebinarRecordingView(ProductView):

    def handouts(self):
        return self.context.getFolderContents({'Type' : 'Webinar Handout'})

    def presentations(self):
        return self.context.getFolderContents({'Type' : 'Webinar Presentation'})

    def speakers(self):
        return getattr(self.context, 'speakers', [])

    def link(self):
        return getattr(self.context, 'link', None)


class EventView(_EventView, ProductView):

    def fmt(self, datestamp):

        if isinstance(datestamp, datetime):
            tz = pytz.timezone(self.context.timezone)
            localized_datetime = datestamp.astimezone(tz)
            return localized_datetime.strftime('%B %d, %Y %I:%M%p').replace(' 0', ' ')

        return 'N/A'

    def start(self):
        return self.fmt(self.context.start)

    def end(self):
        return self.fmt(self.context.end)


class WorkshopView(EventView):

    def pages(self):
        return IWorkshopMarker(self.context).getPageBrains()

class WebinarView(EventView):

    def pages(self):
        return IWebinarMarker(self.context).getPageBrains()

class PublicationView(ProductView):
    pass

class ToolApplicationView(ProductView):
    pass

class CurriculumView(ProductView):
    pass

class WorkshopGroupView(ProductView):
    pass

class WebinarGroupView(ProductView):
    pass

class OnlineCourseView(ProductView):
    pass