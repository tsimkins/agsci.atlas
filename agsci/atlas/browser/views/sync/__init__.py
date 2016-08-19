from agsci.common.utilities import iso_to_datetime
from agsci.atlas.content.sync import SyncContentImporter
from .base import BaseImportContentView

import json
import transaction

# Parent view that accepts a POST of JSON data, and creates or updates a product
# in Plone that is using the same SKU, Plone Id, or Cvent Id

class SyncContentView(BaseImportContentView):

    # Content Importer Object Class
    content_importer = SyncContentImporter

    # Validates the request, and raises an exception if there's an error
    def requestValidation(self):

        # Make sure we have a POST method that has a content type of json
        if self.request.method != 'POST' or \
            not self.request.getHeader('Content-type').startswith('application/json'):

            raise Exception('Request must be a POST of JSON data')

        return True

    # Extracts the JSON POST body, throws exceptions if there is no data, or if
    # the JSON is not valid.  Returns Python dict of JSON data.
    def getDataFromRequest(self):

        json_str = self.request.get("BODY", '')

        if not json_str:
            raise Exception('No JSON data provided.')

        try:
            json_data = json.loads(json_str)

        except ValueError:
            raise Exception('Error parsing JSON data.')

        else:

            # Validate that the JSON data has a `product_type` attribute
            if not json_data.get('product_type', None):
                raise Exception('JSON data does not have "product_type" value.')

            return json_data

    # Runs the import process and returns the JSON data for the item that was
    # created.
    def importContent(self):

        # Create new content importer object
        v = self.content_importer(self.getDataFromRequest())

        # Look up the provided id to see if there's an existing event
        item = self.getProductObject(v)

        # Update the object if it exists
        if item:
            item = self.updateObject(item, v)

            # Commit the transaction after the update so the getJSON() call
            # returns the correct values. This feels like really bad idea, but
            # it appears to works
            transaction.commit()

        # Create the object if it doesn't exist already
        else:
            item = self.createObject(self.import_path, v)

        # Return JSON data
        return self.getJSON(item)

    # Create a new object
    def createObject(self, context, v):
        pass

    # Update existing object
    def updateObject(self, context, v):
        pass

    # Calculates the unique key of the object, based on order of preference of
    # system
    def getProductUniqueKey(self, v):

        # Listing of unique keys by index and value, in order of preference.
        unique_keys = [
            ('UID', v.data.plone_id),
            ('SKU', v.data.sku),
            ('CventId', v.data.cvent_id),
            ('EdxId', v.data.edx_id), # Not currently used.
        ]

        # Iterate through the unique keys, and if there's a value, and the
        # value exists in the catalog index, return that query string.
        for (k, v) in unique_keys:
            if v and v in self.portal_catalog.uniqueValuesFor(k):
                return { k : v }

        raise ValueError('No valid unique id provided')

    # Look up an existing object based on a hierarchy of unique keys in the
    # JSON input
    def getProductObject(self, v):

        try:
            query = self.getProductUniqueKey(v)
        except ValueError:
            return None

        results = self.portal_catalog.searchResults(query)

        if results:
            item = results[0].getObject()

            if v.data.product_type:

                if item.Type() != v.data.product_type:

                    raise Exception('Item with matching key found, but product ' +
                                    'type of "%s" does not match "%s"' % (item.Type(), v.data.product_type))

            return item

        return None

    def getRequestDataAsArguments(self, v):

        # Establish the input arguments. This translates the Magento Attribute
        # key into the Plone field name
        data = {
                    'title' : v.data.name,
                    'description' : v.data.short_description,
                    'start' : iso_to_datetime(v.data.event_start_date),
                    'end' : iso_to_datetime(v.data.event_end_date),
                    'cvent_id' : v.data.cvent_id,
                    'sku' : v.data.sku,
                 }

        # Delete arguments that are explicitly None
        for (k,v) in data.iteritems():
            if v == None:
                del data[k]

        # Return data
        return data
