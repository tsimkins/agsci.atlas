from Products.Five import BrowserView
from plone.app.event.browser.event_view import EventView as _EventView
from agsci.common.utilities import increaseHeadingLevel

class ProductView(BrowserView):

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
        return self.context.getPages()


class ArticleContentView(ProductView):

    pass


class NewsItemView(ArticleView, ArticleContentView):

    pass


class SlideshowView(ArticleContentView):

    def images(self):
        return self.context.getImages()


class VideoView(ArticleContentView):

    def getVideoId(self):
        return self.context.getVideoId()

    def getVideoProvider(self):
        return self.context.getVideoProvider()


class WebinarRecordingView(ProductView):

    def handouts(self):
        return self.context.getFolderContents({'Type' : 'Webinar Handout'})

    def presentations(self):
        return self.context.getFolderContents({'Type' : 'Webinar Presentation'})

    def speakers(self):
        return getattr(self.context, 'speakers', [])

    def link(self):
        return getattr(self.context, 'link', None)


class EventView(_EventView):

    pass


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