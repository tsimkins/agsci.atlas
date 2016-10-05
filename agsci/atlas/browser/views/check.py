from Products.statusmessages.interfaces import IStatusMessage
from Products.Five import BrowserView
from plone.memoize.view import memoize
from zope.component import subscribers

from agsci.atlas.constants import ACTIVE_REVIEW_STATES
from agsci.atlas.content.check import IContentCheck
from agsci.atlas.content.check import getValidationErrors
from .base import BaseView

from .helpers import ProductTypeChecks

import urllib

# This view will show all of the automated checks by product type

class EnumerateErrorChecksView(BaseView):

    review_state = ACTIVE_REVIEW_STATES

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
            checks = []

            for c in subscribers((context,), IContentCheck):
                if self.show_all or self.getIssueCount(pt, c) > 0:
                    checks.append(c)

            checks.sort(key=lambda x: x.sort_order)

            # Append a new ProductTypeChecks to the return list
            data.append(ProductTypeChecks(pt, checks))

        return data

    @property
    def show_all(self):
        return not not self.request.form.get('all', None)

    @property
    @memoize
    def issueSummary(self):
        data = {}

        results = self.portal_catalog.searchResults({'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                                                     'review_state' : self.review_state})

        for r in results:
            if not data.has_key(r.Type):
                data[r.Type] = {}
            if r.ContentErrorCodes:
                for i in r.ContentErrorCodes:
                    if not data[r.Type].has_key(i):
                        data[r.Type][i] = 0
                    data[r.Type][i] = data[r.Type][i] + 1
        return data

    def getErrorListingURL(self, ptc, c):
        product_type = ptc.product_type
        error_code = c.error_code
        params = urllib.urlencode({'Type' : product_type, 'ContentErrorCodes' : error_code})
        return '%s/@@content_check_items?%s' % (self.context.absolute_url(), params)

    def getIssueCount(self, ptc, c):
        if isinstance(ptc, ProductTypeChecks):
            product_type = ptc.product_type
        else:
            product_type = ptc
        error_code = c.error_code
        return self.issueSummary.get(product_type, {}).get(error_code, 0)


class ContentCheckItemsView(EnumerateErrorChecksView):

    def getFolderContents(self, contentFilter={}):
        query = {}
        query.update(contentFilter)
        query.update(self.request.form)
        query['sort_on'] = 'sortable_title'
        query['review_state'] = self.review_state
        return self.portal_catalog.searchResults(query)

    @property
    def show_description(self):
        return True

    @property
    def show_image(self):
        return True

    @property
    def hasTiledContents(self):
        return True

    @property
    def getTileColumns(self):
        return '4'

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