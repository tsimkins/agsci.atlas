from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

class ArticleView(BrowserView):

    def pages(self):
        return self.context.listFolderContents({'Type' : 'Article Page'})


class ArticlePageView(BrowserView):

    pass


class WebinarRecordingView(BrowserView):

    def handouts(self):
        return self.context.getFolderContents({'Type' : 'Webinar Handout'})

    def presentations(self):
        return self.context.getFolderContents({'Type' : 'Webinar Presentation'})

    def speakers(self):
        return getattr(self.context, 'speakers', [])

    def link(self):
        return getattr(self.context, 'link', None)