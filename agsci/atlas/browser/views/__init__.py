from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.event.browser.event_view import EventView as _EventView
from plone.memoize.instance import memoize
from zope.component import subscribers

from agsci.common.browser.views import FolderView
from agsci.atlas.content.check import IContentCheck
from agsci.common.utilities import increaseHeadingLevel
from agsci.atlas.content.check import getValidationErrors
from agsci.atlas.content.sync.product import AtlasProductImporter
from agsci.atlas.interfaces import IPDFDownloadMarker

class ProductTypeChecks(object):
    
    def __init__(self, product_type='', checks=[]):
        self.product_type = product_type
        self.checks = checks

# This view will show all of the automated checks by product type
class EnumerateErrorChecksView(FolderView):

    def getChecksByType(self):

        # initialize return list
        data = []

        # Search for all of the Atlas Products
        results = self.portal_catalog.searchResults({'object_provides' : 
                                                     'agsci.atlas.content.IAtlasProduct'})
        
        # Get a unique list of product types
        product_types = set([x.Type for x in results])
        
        # Iterate through the unique types, grab the first object of that 
        # type from the results
        for pt in sorted(product_types):
        
            # Get a list of all objects of that product type
            products = filter(lambda x: x.Type == pt, results)
            
            # Grab the first element (brain) in that list
            r = products[0]
            
            # Grab the object for the brain
            context = r.getObject()
            
            # Get content checks
            checks = subscribers((context,), IContentCheck)

            # Append a new ProductTypeChecks to the return list
            data.append(ProductTypeChecks(pt, checks))
        
        return data



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


class ContentByReviewState(object):

    key = 'review_state'
    sort_order = ['imported', 'requires_initial_review', 'private',
                  'pending', 'published', 'expiring-soon', 'expired']

    key_2 = 'Type'

    def __init__(self, results):
        self.results = results

    def getSortOrder(self, x):

        try:
            return self.sort_order.index(x.get(self.key, ''))
        except ValueError:
            return 99999

    def __call__(self):

        data = {}

        for r in self.results:

            k = getattr(r, self.key)

            if not data.has_key(k):
                data[k] = {self.key : k, 'brains' : []}

            data[k]['brains'].append(r)

        if self.key_2:
            for k in data.keys():
                data[k]['brains'].sort(key=lambda x: getattr(x, self.key_2, ''))

        return sorted(data.values(), key=self.getSortOrder)

class ContentByType(ContentByReviewState):

    key = 'Type'
    sort_order = ['Article', 'Publication']

    key_2 = 'review_state'

    @memoize
    def product_types(self):
        return sorted(list(set([x.Type for x in self.results])))

    @property
    def sort_order(self):
        return self.product_types()

class UserContentView(FolderView):

    content_structure_factory = ContentByReviewState

    def getFolderContents(self, **contentFilter):

        query = {'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                 'sort_on' : 'sortable_title'}

        user_id = self.getUserId()

        if user_id:
            query['Owners'] = user_id

        return self.portal_catalog.searchResults(query)

    def getContentStructure(self, **contentFilter):

        results = self.getFolderContents(**contentFilter)

        v = self.content_structure_factory(results)

        return v()

    def getType(self, brain):
        return brain.Type.lower().replace(' ', '')
    
    def getIssues(self, brain):
        issues = brain.ContentIssues
        
        levels = ['High', 'Medium', 'Low']
        
        if issues:
            rv = []

            data = dict(zip(levels, issues))
            
            for k in levels:
                v = data.get(k)
                
                if isinstance(v, int) and v > 0:
                    rv.append(v*('<span class="error-check-%s"></span>' % k.lower()))
            if rv:
                return "".join(rv)

            return '<span class="error-check-none"></span>'


class AllContentView(UserContentView):

    content_structure_factory = ContentByType

    def getUserId(self):

        return None

class OldPloneView(FolderView):
    
    def __call__(self):
    
        uid = self.request.form.get('UID', None)
        
        if not uid:
            raise Exception('UID not provided')
        
        results = self.portal_catalog.searchResults({'OriginalPloneIds' : uid})
        
        if not results:
            raise Exception('Old Plone UID %s not found' % uid)            
        
        url = results[0].getURL()

        self.request.response.redirect(url)

class ToOldPloneView(FolderView):
    
    @property
    def original_plone_ids(self):
        return getattr(self.context, 'original_plone_ids', [])
    
    def __call__(self):
    
        uids = self.original_plone_ids
        
        if not uids:
            raise Exception('UID not provided')
        
        for uid in uids:
            v = AtlasProductImporter(uid)
            
            try:
                url = v.data.url
            except:
                pass
            else:
                if url:
                    url = url.replace('http://', 'https://')
                    self.request.response.redirect(url)
                    return True

        raise Exception("Could not find content in old Plone site")