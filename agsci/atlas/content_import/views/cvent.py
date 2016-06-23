from Products.Five import BrowserView
from agsci.api.utilities import iso_to_datetime, default_timezone
from plone.app.event.dx.behaviors import EventAccessor
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.event.interfaces import IEventAccessor
from zope.interface import alsoProvides

import json

from . import ImportContentView
from ..cvent import CventContentImporter

# Accessor subclass for event
class AtlasComplexWorkshopAccessor(EventAccessor):
    event_type = 'atlas_complex_workshop'

# Factory that takes in product type and returns the correct accessor subclass
# Currently just returns the complex workshop
def AtlasEventAccessorFactory(product_type):
    return AtlasComplexWorkshopAccessor

# View that accepts a POST of JSON data, and creates an event in Plone that 
# references the Cvent event id.
class ImportCventView(ImportContentView):

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

        # Create new content importer object
        v = CventContentImporter(self.getDataFromRequest())

        # Create the Cvent event
        product_type = 'atlas_complex_workshop'
        item = self.createCventEvent(self.import_path, product_type, v)
        
        # Return JSON data
        return self.getJSON(item)

    # Create the Plone object for the event, and return the object that was
    # created.
    def createCventEvent(self, context, product_type, v):
        
        # Get the accessor class
        acc_klass = AtlasEventAccessorFactory(product_type)

        # Establish the input arguments
        kwargs = {
                    'timezone' : default_timezone,
                    'title' : v.data.name,
                    'description' : v.data.short_description,
                    'start' : iso_to_datetime(v.data.event_start_date),
                    'end' : iso_to_datetime(v.data.event_end_date),
                 }

        # Create the object
        # http://docs.plone.org/external/plone.app.event/docs/development.html
        acc = acc_klass.create(context, v.data.cvent_id, 
                               whole_day=False, open_end=False, **kwargs)

        # Pass the arguments into the object
        acc.edit(**kwargs)

        # Set the body text for the object
        acc.context.text = RichTextValue(raw=v.data.description, 
                          mimeType=u'text/html', 
                          outputMimeType='text/x-html-safe')
        
        # Reindex the object
        acc.context.reindexObject()

        # Return object that was created
        return acc.context