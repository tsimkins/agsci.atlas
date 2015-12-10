from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from agsci.common.utilities import increaseHeadingLevel
from agsci.atlas.interfaces import IArticleMarker, IVideoMarker, ISlideshowMarker

class ArticleView(BrowserView):

    def pages(self):
        return IArticleMarker(self.context).getPages()

class ArticleContentView(BrowserView):

    def getText(self, adjust_headings=False):
        text = self.context.text.output

        if adjust_headings:
            return increaseHeadingLevel(text)

        return text


class SlideshowView(ArticleContentView):

    def images(self):
        return ISlideshowMarker(self.context).getImages()


class VideoView(ArticleContentView):

    def getVideoId(self):
        return IVideoMarker(self.context).getVideoId()

    def getVideoProvider(self):
        return IVideoMarker(self.context).getVideoProvider()


class WebinarRecordingView(BrowserView):

    def handouts(self):
        return self.context.getFolderContents({'Type' : 'Webinar Handout'})

    def presentations(self):
        return self.context.getFolderContents({'Type' : 'Webinar Presentation'})

    def speakers(self):
        return getattr(self.context, 'speakers', [])

    def link(self):
        return getattr(self.context, 'link', None)


