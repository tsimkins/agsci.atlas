from agsci.common.utilities import iso_to_datetime
from agsci.atlas.content.accessors import AtlasEventAccessorFactory
from plone.app.textfield.value import RichTextValue
from plone.event.interfaces import IEventAccessor
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import json

from . import SyncContentView

# View that accepts a POST of JSON data, and creates an event in Plone that
# references the Cvent event id.
class SyncCventView(SyncContentView):

    # Update existing event
    def updateObject(self, context, v):

        # Get the accessor object
        acc = IEventAccessor(context)

        # Establish the input arguments
        kwargs = self.getRequestDataAsArguments(v)

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
    def createObject(self, context, v):

        # Get the accessor class
        acc_klass = AtlasEventAccessorFactory(v.data.product_type)

        # Establish the input arguments
        kwargs = self.getRequestDataAsArguments(v)

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
