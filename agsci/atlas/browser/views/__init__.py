from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.event.browser.event_view import EventView as _EventView

from agsci.common.browser.views import FolderView
from agsci.common.utilities import increaseHeadingLevel
from agsci.atlas.content.check import getValidationErrors
from agsci.atlas.interfaces import IPDFDownloadMarker

class ErrorCheckView(BrowserView):

    def __call__(self):

        errors = getValidationErrors(self.context)

        if errors:

            if errors[0].level in ('High', 'Medium'):

                message = 'You cannot submit this product for publication until <a href="#data-check">a few issues are resolved</a>.'
                message_type = 'warning'
            else:
                message = 'Please try to resolve <a href="#data-check">any content issues</a>.'
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

class PDFDownloadView(FolderView):

    def __call__(self):

        # If we're an anonymous user, and getPDF errors, send an email, and
        # return a boring and unhelpful error message.  If we're logged in, let
        # the error happen.

        if self.anonymous:

            try:
                (pdf, filename) = IPDFDownloadMarker(self.context).getPDF()
            except:
                # Send email
                #emailUsers = ['webservices@ag.psu.edu']
                emailUsers = ['trs22@psu.edu']
                mFrom = "do.not.reply@psu.edu"
                mSubj = "Error auto-generating PDF: %s" % self.context.Title()
                mMsg = '<p><strong>ERROR:</strong> <a href="%s">%s</a></p>'  % (self.context.absolute_url(), self.context.Title())
                mailHost = self.context.MailHost

                for mTo in emailUsers:
                    mailHost.secureSend(mMsg.encode('utf-8'), mto=mTo, mfrom=mFrom, subject=mSubj, subtype='html')

                # Return error message
                return "<h1>Error</h1><p>Sorry, an error has occurred.</p>"

        else:
            (pdf, filename) = IPDFDownloadMarker(self.context).getPDF()

        if pdf:
            self.request.response.setHeader('Content-Type', 'application/pdf')
            self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % filename)

            return pdf

        return "<h1>Error</h1><p>No PDF download available.</p>"

class UserContentView(FolderView):

    def getFolderContents(self, **contentFilter):

        query = {'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                 'sort_on' : 'sortable_title'}

        user_id = self.getUserId()

        if user_id:
            query['Owners'] = user_id

        return self.portal_catalog.searchResults(query)

    def getContentStructure(self, **contentFilter):
        
        results = self.getFolderContents(**contentFilter)
        
        v = ContentByReviewState(results)
        
        return v()


class ContentByReviewState(object):
    
    def __init__(self, results):
        self.results = results
    
    def __call__(self):
    
        def getSortOrder(x):
            sort_order = ['imported', 'requires_initial_review', 'private',
                          'pending', 'published', 'expiring-soon', 'expired']
            
            try:
                return sort_order.index(x.get('review_state', ''))
            except ValueError:
                return 99999
    
        data = {}
        
        for r in self.results:

            if not data.has_key(r.review_state):
                data[r.review_state] = {'review_state' : r.review_state, 'brains' : []}

            data[r.review_state]['brains'].append(r)
        
        return sorted(data.values(), key=getSortOrder)