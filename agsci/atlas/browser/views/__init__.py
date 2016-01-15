from plone.app.event.browser.event_view import EventView as _EventView
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from agsci.api.utilities import increaseHeadingLevel

class ArticleView(BrowserView):

    def pages(self):
        return self.context.getPages()


class ArticleContentView(BrowserView):

    def getText(self, adjust_headings=False):
        text = self.context.text.output

        if adjust_headings:
            return increaseHeadingLevel(text)

        return text


class SlideshowView(ArticleContentView):

    def images(self):
        return self.context.getImages()


class VideoView(ArticleContentView):

    def getVideoId(self):
        return self.context.getVideoId()

    def getVideoProvider(self):
        return self.context.getVideoProvider()


class WebinarRecordingView(BrowserView):

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