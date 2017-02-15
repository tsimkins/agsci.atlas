from agsci.atlas.content.accessors import AtlasEventAccessorFactory
from dateutil import parser as date_parser
from plone.app.textfield.value import RichTextValue
from plone.event.interfaces import IEventAccessor
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import WrongType
from zope import schema

from . import SyncContentView

from agsci.atlas.utilities import default_timezone
from agsci.atlas.content.event.cvent import ICventProductDetailRowSchema

import pytz

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

        # Update complex fields (text, event agenda)
        self.updateComplexFields(acc.context, v)

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

        # Update complex fields (text, event agenda)
        self.updateComplexFields(acc.context, v)

        # Reindex the object
        acc.context.reindexObject()

        # Ref: http://docs.plone.org/external/plone.app.event/docs/development.html#accessing-event-objects-via-an-unified-accessor-object
        # Throw ObjectModifiedEvent after setting properties to call an event subscriber which does some timezone related post calculations
        notify(ObjectModifiedEvent(acc.context))

        # Return object that was created
        return acc.context

    def updateComplexFields(self, context, v):

        # Set the body text for the object
        context.text = RichTextValue(raw=v.data.description,
                          mimeType=u'text/html',
                          outputMimeType='text/x-html-safe')

        # Update the agenda
        if v.data.product_detail:

            # Validate input data
            if not isinstance(v.data.product_detail, list):
                raise TypeError('product_detail is not an array')

            else:
                for i in v.data.product_detail:

                    if not isinstance(i, dict):
                        raise TypeError('product_detail item is not an associative array')
                    else:
                        # Validate incoming data structure against
                        # ICventProductDetailRowSchema

                        # Check for extra keys
                        input_keys = set(i.keys())
                        expected_keys = set(ICventProductDetailRowSchema.names())

                        extra_keys = list(input_keys - expected_keys)

                        if extra_keys:
                            raise ValueError('product_detail has extra keys %s' % repr(extra_keys))

                        # Check for valid data types
                        for (field_name, field) in ICventProductDetailRowSchema.namesAndDescriptions():
                            if i.has_key(field_name):

                                # Pre-process datetimes
                                if isinstance(field, schema.Datetime):
                                    try:
                                        field_value = date_parser.parse(i[field_name])
                                    except:
                                        # Let the validation catch it. Not a datetime
                                        pass
                                    else:
                                        # if it's a naive timezone, set it to Eastern
                                        if not field_value.tzinfo:
                                            i[field_name] =  pytz.timezone(default_timezone).localize(field_value)
                                        else:
                                            i[field_name] = field_value

                                # Strip whitespace from strings
                                if isinstance(i[field_name], (str, unicode)):
                                    i[field_name] = i[field_name].strip()

                                # Run the validation for the schema field against
                                # the incoming data
                                try:
                                    field.validate(i[field_name])

                                except WrongType, e:
                                    raise ValueError("Wrong type for %s: expected %s, not %s" % (field_name, e.args[1].__name__, e.args[0].__class__.__name__))

                                except:
                                    raise ValueError("Error with %s" % field_name)

            # Set event agenda to product_detail
            context.product_detail = v.data.product_detail