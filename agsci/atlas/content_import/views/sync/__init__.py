from agsci.common.utilities import iso_to_datetime

import json

from .. import ImportContentView

# Parent view that accepts a POST of JSON data, and creates or updates a product
# in Plone that is using the same SKU, Plone Id, or Cvent Id

class SyncContentView(ImportContentView):

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
            return json_data

    # Runs the import process and returns the JSON data for the item that was
    # created.
    def importContent(self):

        return '{}' # Empty JSON

    # Look up an existing object based on a hierarchy of unique keys in the
    # JSON input
    def getProductObject(self, v):

        query = {}

        if v.data.sku:
            query['SKU'] = v.data.sku

        elif v.data.plone_id:
            query['UID'] = v.data.plone_id

        elif v.data.cvent_id:
            query['CventId'] = v.data.cvent_id

        elif v.data.edx_id: # Not currently used.
            query['EdxId'] = v.data.edx_id

        else:
            raise ValueError('No unique id provided')

        results = self.portal_catalog.searchResults(query)

        if results:
            item = results[0].getObject()

            if item.Type() != v.data.product_type:
                raise Exception('Item with matching key found, but product type of' +
                                '%s does not match %s' % (item.Type(), v.data.product_type))

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
                 }

        # Delete arguments that are explicitly None
        for (k,v) in data.iteritems():
            if v == None:
                del data[k]

        # Return data
        return data