from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.event.browser.event_view import EventView as _EventView

from agsci.api.utilities import increaseHeadingLevel
from agsci.atlas.content.check import getValidationErrors

class ErrorCheckView(BrowserView):
    
    def __call__(self):

        errors = getValidationErrors(self.context)
        
        if errors:

            if errors[0].level in ('High', 'Medium'):
    
                message = 'You cannot submit this product for publication until a few issues are resolved.'
                message_type = 'warning'
            else:
                message = 'Please try to resolve any content issues.'
                message_type = 'info'
    
            IStatusMessage(self.request).addStatusMessage(message, type=message_type)

            if message_type in ('warning',):
                return False
        
        return True

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