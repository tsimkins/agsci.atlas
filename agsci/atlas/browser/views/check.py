from Products.statusmessages.interfaces import IStatusMessage
from Products.Five import BrowserView
from zope.component import subscribers

from agsci.atlas.content.check import IContentCheck
from agsci.atlas.content.check import getValidationErrors
from .base import BaseView

from .helpers import ProductTypeChecks

# This view will show all of the automated checks by product type

class EnumerateErrorChecksView(BaseView):

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