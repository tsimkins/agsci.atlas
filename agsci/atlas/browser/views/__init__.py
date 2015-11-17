from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from agsci.common.utilities import increaseHeadingLevel

class ArticleView(BrowserView):

    def pages(self):
        return self.context.listFolderContents({'Type' : ['Slideshow', 'Article Page']})

class ArticleContentView(BrowserView):

    def getText(self, adjust_headings=False):
        text = self.context.text.output

        if adjust_headings:
            return increaseHeadingLevel(text)

        return text

    def images(self):
        return self.context.listFolderContents({'Type' : 'Image'})


class WebinarRecordingView(BrowserView):

    def handouts(self):
        return self.context.getFolderContents({'Type' : 'Webinar Handout'})

    def presentations(self):
        return self.context.getFolderContents({'Type' : 'Webinar Presentation'})

    def speakers(self):
        return getattr(self.context, 'speakers', [])

    def link(self):
        return getattr(self.context, 'link', None)


