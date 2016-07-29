from agsci.common.utilities import iso_to_datetime, default_timezone
from agsci.atlas.content.accessors import AtlasEventAccessorFactory
from plone.app.textfield.value import RichTextValue
from plone.event.interfaces import IEventAccessor
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import json
import transaction

from . import ImportContentView
from ..cvent import CventContentImporter

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

        # Look up the provided id to see if there's an existing event
        existing_cvent_event = self.getEventByCventId(v.data.cvent_id)

        # Update the Cvent event if it exists
        if existing_cvent_event:
            item = self.updateCventEvent(existing_cvent_event, v)

            # Commit the transaction after the update so the getJSON() call
            # returns the correct values. This feels like really bad idea, but
            # it appears to works
            transaction.commit()

        # Create the Cvent event if it doesn't exist already
        else:
            product_type = 'atlas_cvent_event'
            item = self.createCventEvent(self.import_path, product_type, v)

        # Return JSON data
        return self.getJSON(item)

    # Lookup an existing event with the specified Cvent id
    def getEventByCventId(self, cvent_id):

        if not cvent_id:
            raise ValueError('No Cvent Id provided')

        results = self.portal_catalog.searchResults({'CventId' : cvent_id})

        if results:
            return results[0].getObject()

        return None

    def getEventDataAsArguments(self, v):
        # Establish the input arguments

        return {
                    'timezone' : default_timezone,
                    'title' : v.data.name,
                    'description' : v.data.short_description,
                    'start' : iso_to_datetime(v.data.event_start_date),
                    'end' : iso_to_datetime(v.data.event_end_date),
                    'cvent_id' : v.data.cvent_id,
                 }

    # Update existing event
    def updateCventEvent(self, context, v):

        # Get the accessor object
        acc = IEventAccessor(context)

        # Establish the input arguments
        kwargs = self.getEventDataAsArguments(v)

        # Pass the arguments into the object
        acc.edit(**kwargs)

        # Update any arguments that are not part of the default event schema
        acc.update(**kwargs)

        # Reindex the object
        acc.context.reindexObject()

        # Ref: http://docs.plone.org/external/plone.app.event/docs/development.html#accessing-event-objects-via-an-unified-accessor-object
        # Throw ObjectModifiedEvent after setting properties to call an event subscriber which does some timezone related post calculations
        notify(ObjectModifiedEvent(acc.context))

        # Return object that was updated
        return acc.context

    # Create the Plone object for the event, and return the object that was
    # created.
    def createCventEvent(self, context, product_type, v):

        # Get the accessor class
        acc_klass = AtlasEventAccessorFactory(product_type)

        # Establish the input arguments
        kwargs = self.getEventDataAsArguments(v)

        # Create the object
        # http://docs.plone.org/external/plone.app.event/docs/development.html
        acc = acc_klass.create(context, v.data.cvent_id,
                               whole_day=False, open_end=False, **kwargs)

        # Update any arguments that are not part of the default event schema
        acc.update(**kwargs)

        # Set the body text for the object
        acc.context.text = RichTextValue(raw=v.data.description,
                          mimeType=u'text/html',
                          outputMimeType='text/x-html-safe')

        # Reindex the object
        acc.context.reindexObject()

        # Ref: http://docs.plone.org/external/plone.app.event/docs/development.html#accessing-event-objects-via-an-unified-accessor-object
        # Throw ObjectModifiedEvent after setting properties to call an event subscriber which does some timezone related post calculations
        notify(ObjectModifiedEvent(acc.context))

        # Return object that was created
        return acc.context
