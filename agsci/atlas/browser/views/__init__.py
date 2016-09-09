from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import subscribers

from agsci.common.browser.views import FolderView
from agsci.atlas.content.check import IContentCheck
from agsci.atlas.content.check import getValidationErrors
from agsci.atlas.content.sync.product import AtlasProductImporter
from agsci.atlas.interfaces import IPDFDownloadMarker

from helpers import ProductTypeChecks, ContentByReviewState, ContentByType, ContentByAuthorTypeStatus

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


class ContentByAuthorTypeStatusView(UserContentView):

    content_structure_factory = ContentByAuthorTypeStatus

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