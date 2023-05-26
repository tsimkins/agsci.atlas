from Products.CMFCore.utils import getToolByName
from collective.z3cform.datagridfield.row import DictRow
from dateutil import parser as date_parser
from decimal import Decimal
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.field import NamedBlobImage
from zope.component import getMultiAdapter
from zope.event import notify
from zope.schema.interfaces import WrongType, ConstraintNotSatisfied
from zope import schema

from agsci.atlas.constants import DEFAULT_TIMEZONE, IMAGE_FORMATS, DELIMITER
from agsci.atlas.utilities import getAllSchemaFieldsAndDescriptionsForType, getAllSchemaFieldsAndDescriptions
from agsci.atlas.content.sync import SyncContentImporter
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.events.interfaces import AtlasImportEvent

from .base import BaseImportContentView

import base64
import json
import pprint
import pytz
import transaction

pp = pprint.PrettyPrinter(indent=4)

# Parent view that accepts a POST of JSON data, and creates or updates a product
# in Plone that is using the same SKU, Plone Id, or Cvent Id

class SyncContentView(BaseImportContentView):

    # Product Type (Human)
    product_type = None

    # Content Importer Object Class
    content_importer = SyncContentImporter

    # Define 'complex' (i.e. grid) fields
    complex_fields = []

    # Can create object?
    can_create = True

    # Based on the human-readable `product_type` .Type() from the JSON data, get
    # the Plone .portal_type from portal_types
    #
    # If a `product_type` isn't provided by the JSON data, use the default from
    # the view if it exists
    def getPortalType(self, v):

        product_type = v.data.product_type

        if not product_type:
            product_type = self.product_type

        if product_type:

            portal_types = getToolByName(self.context, 'portal_types')

            pt = portal_types.listTypeInfo()

            # First, product type and atlas_ factory matches.
            matching = [x for x in pt if x.Title() == product_type and x.factory.startswith('atlas_')]

            # Then, all matches
            matching.extend([x for x in pt if x.Title() == product_type])

            # If we have a match, return the title of the first match
            if matching:
                return matching[0].factory

        return None

    # Validates the request, and raises an exception if there's an error
    def requestValidation(self):

        # Make sure we have a POST method that has a content type of json
        if self.request.method != 'POST' or \
            not self.request.getHeader('Content-type', '').lower().startswith('application/json'):

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
            raise Exception('Error parsing JSON data.:\n-----\n%s\n-----\n' % json_str)

        else:
            # Log incoming JSON
            if self.debug:
                self.log('Called with JSON', detail='\n-----\n%s\n-----\n' % json_str)

            # If we're passed in a dict via JSON, convert it to a list
            if isinstance(json_data, dict):
                json_data = [json_data,]

            return json_data

    # Runs the import process and returns the JSON data for the item that was
    # created.
    def importContent(self):

        # Get request data
        try:
            request_data = self.getDataFromRequest()
        except Exception as e:
            return self.HTTPError(str(e))

        # Create a list (rv) for return values of objects
        rv = []

        # Iterate through the list of objects to update, and import them
        for i in request_data:

            # Create new content importer object
            v = self.content_importer(i)

            # Import the object
            item = self.importObject(v)

            # If we have an item returned...
            if item:

                # Append the created/updated item to the rv list
                rv.append(item)

                # Notify that this item has been imported
                notify(AtlasImportEvent(item))

        # Commit the transaction after the update/create so the getJSON() call
        # returns the correct values. This feels like really bad idea, but
        # it appears to work.
        transaction.commit()

        # Return the JSONified version of the list of items
        return self.getJSON(rv)

    # Given a content importer (v), attempts to
    def importObject(self, v):

        # Log call
        log_msg = "Importing object: %s" % v.data.name

        if self.debug:
            self.log(log_msg, detail=pp.pformat(v.json_data))
        else:
            self.log(log_msg)

        # Look up the provided id to see if there's an existing event
        item = self.getProductObject(v)

        # Update the object if it exists
        if item:
            item = self.updateObject(item, v)

        # Create the object if it doesn't exist already
        elif self.can_create:

            # Quick test to see if we have at least a 'product_type' and
            # 'name' fields.
            if not (v.data.name and v.data.product_type):
                raise Exception("Minimum required fields of 'title' and 'product_type' not present in JSON: %s", pp.pformat(v.json_data))

            item = self.createObject(self.import_path, v)

        # This view is set to not create products, so we'll log the error and
        # return a null value.
        else:
            self.log("Existing product not found. Will not create product.\n%s" % pp.pformat(v.json_data))
            return None

        # Update the Rich text field, if we're passed a 'description' key.
        if v.data.description:
            item.text = RichTextValue(raw=v.data.description,
                                      mimeType=u'text/html',
                                      outputMimeType='text/x-html-safe')

        # Handle leadimage field
        if v.data.leadimage:

            item.leadimage = self.to_image_field(v.data.leadimage)

            leadimage_caption = v.data.leadimage.get('caption', None)

            if isinstance(leadimage_caption, (str, )):
                item.leadimage_caption = leadimage_caption

        # Handle categories
        if v.data.categories:

            for (_k, _v) in self.categories(v).items():
                setattr(item, _k, _v)

        # Handle Extension structure
        if v.data.extension_structure:

            for (_k, _v) in self.extension_structure(v).items():
                setattr(item, _k, _v)

        # Return JSON data
        return item

    # Create a new object
    def createObject(self, context, v):

        portal_type = self.getPortalType(v)

        if not portal_type:
            raise Exception("No valid portal_type found for product type %s" % v.data.product_type)

        kwargs = self.getRequestDataAsArguments(v)

        item = createContentInContainer(
                context,
                portal_type,
                id=self.getId(v),
                **kwargs)

        self.updateComplexFields(context, v)

        return item

    # Update existing object
    def updateObject(self, context, v):

        updated = False

        # Establish the input arguments
        kwargs = self.getRequestDataAsArguments(v, context)

        for (_k,_v) in kwargs.items():

            # Skip if it's a 'complex' field
            if _k in self.complex_fields:
                continue

            # Check if the existing value is equal.  If not, update and set
            # flag to true
            if getattr(context, _k, None) != _v:
                setattr(context, _k, _v)
                updated = True

        # Run the updates for complex (i.e. grid) fields.  If that returns a
        # true value (there were updates) then set the flag to true
        if self.updateComplexFields(context, v):
            updated = True

        # If the updated flag is true, reindex the object.
        if updated:
            context.reindexObject()

        return context

    # Method for updating complex (i.e. grid) fields
    def updateComplexFields(self, context, v):
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

        # If we're a person, also check the short name ('getId') value for the
        # SKU provided
        if v.data.product_type in ['Person',]:
            unique_keys.append(
                ('getId', v.data.sku),
            )
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

        product_type = self.getPortalType(v)

        if product_type:
            query['portal_type'] = product_type

        results = self.portal_catalog.searchResults(query)

        if results:
            return results[0].getObject()

        return None

    def getRequestDataAsArguments(self, v, item=None):

        # Get the API view
        api_view = getMultiAdapter((self.context, self.request), name='api')

        # Get the portal_type from the item.  If an item is not provided, get it
        # from the product_type (.Type()) in JSON.
        if item and hasattr(item, 'portal_type') and item.portal_type:
            portal_type = item.portal_type
        else:
            portal_type = self.getPortalType(v)

        # List of arguments to return
        data = {}

        # Iterate through all schema fields, validate, and insert into return data
        for (field_name, field) in getAllSchemaFieldsAndDescriptionsForType(portal_type):

            # Convert Plone field name to API key
            api_field_name = api_view.rename_key(field_name)

            # Get the field value from input data
            field_value = getattr(v.data, api_field_name)

            # Validate (with any necessary transforms) field value
            field_value = self.validateField(field, field_value)

            # Continue if the field value is a literal None or empty
            if field_value in (None, ''):
                continue

            # Push that value back into the data dict
            data[field_name] = field_value

        # Additional logging in debug mode
        if self.debug:

            # Log keys that aren't used. Description is custom, and product_type
            # isn't used so we're ignoring that.
            unused_keys = list(set(v.data.data.keys()) - \
                               set(['description', 'product_type']) - \
                               set([api_view.rename_key(x) for x in data.keys()]))

            unused_keys = dict([(x, getattr(v.data, x)) for x in unused_keys if getattr(v.data, x)])

            if unused_keys:
                self.log("Unused keys from API call.", detail=pp.pformat(unused_keys))

        # Return data
        return data

    # Given a schema field and a value, do any necessary transforms, and validate it
    def validateField(self, field, field_value):

        # Pre-process datetimes
        if isinstance(field, schema.Datetime):

            # Don't try to process an empty DateTime.  It comes back as "now".
            if not field_value:
                return None

            try:
                field_value = date_parser.parse(field_value)
            except:
                # Let the validation catch it. Not a datetime
                return None
            else:
                # if it's a naive timezone, set it to Eastern
                if not field_value.tzinfo:
                    field_value =  pytz.timezone(DEFAULT_TIMEZONE).localize(field_value)

        # Pre-process incoming numeric (int, float) fields into decimals
        if isinstance(field, schema.Decimal):
            if isinstance(field_value, (float, int)):
                field_value = Decimal('%0.2f' % field_value)

        # Pre-process blob image fields
        if isinstance(field, NamedBlobImage) and not isinstance(field_value, NamedBlobImage):
            field_value = self.to_image_field(field_value)

        # Validate a data grid field (indicated by a value_type of DictRow)
        value_type = getattr(field, 'value_type', None)

        if isinstance(value_type, DictRow):

            _schema = getattr(value_type, 'schema', None)

            if _schema:
                for i in range(0, len(field_value)):

                    for (_name, _field) in getAllSchemaFieldsAndDescriptions(_schema):

                        if hasattr(field_value[i], _name):
                            _value = field_value[i][_name]
                            field_value[i][_name] = self.validateField(_field, _value)

            return field_value

        # Strip whitespace from strings
        if isinstance(field_value, (str, )):
            field_value = field_value.strip()

        # If the field value is empty, return it
        if field_value in (None, ''):
            return field_value

        # If the schema field is a list/tuple, but the value is a string, convert
        # the string to a list.
        if isinstance(field, (schema.List, schema.Tuple)) and \
           isinstance(field_value, (str, )):
            field_value = [field_value, ]

        # If the field value is a list/tuple, filter out null values.
        if isinstance(field_value, (list, tuple)):
            field_value = [x for x in field_value if not isinstance(x, type(None))]

        # Run the validation for the schema field against
        # the incoming data
        try:
            field.validate(field_value)

        except WrongType as e:
            raise ValueError("Wrong type for %s: expected %s, not %s" % (field.__name__, e.args[1].__name__, e.args[0].__class__.__name__))

        except ConstraintNotSatisfied as e:
            raise ValueError("Invalid value for '%s': %s" % (field.__name__, str(e)))

        except Exception as e:
            raise ValueError("%s error for '%s': %s" % (e.__class__.__name__, field.__name__, str(e)))

        else:
            return field_value

    def to_image_field(self, value):

        if isinstance(value, dict):
            image_data = value.get('data', None)
            image_mimetype = value.get('mimetype', '')

            if image_data:
                image_data = base64.b64decode(image_data)

                v = self.content_importer({})

                _extension = IMAGE_FORMATS.get(image_mimetype, [None, 'data'])[1]

                filename = value.get('filename', 'image.%s' % _extension)

                return v.data_to_image_field(
                    image_data,
                    contentType=image_mimetype,
                    filename=filename
                )
        elif isinstance(value, NamedBlobImage):
            return value

    def categories(self, v):
        key_fmt = 'atlas_category_level_%d'
        rv = dict([(key_fmt % x, []) for x in range(1,4)])

        for _c in v.data.categories:

            # Skip the first (L0) level
            for i in range(1, len(_c)):
                k = key_fmt % i
                v = DELIMITER.join(_c[1:i+1])
                rv[k].append(v)

        for i in range(1,4):
            k = key_fmt % i
            content_type = u"CategoryLevel%d"% i
            mc = AtlasMetadataCalculator(content_type)
            terms = mc.getTermsForType()
            rv[k] = list(set(rv[k]) & set([x.value for x in terms]))

        return rv

    def extension_structure(self, v):

        key_fmt = 'atlas_%s'

        fields = [
            "state_extension_team",
            "program_team",
            "curriculum",
        ]

        rv = dict([(key_fmt % x, []) for x in fields])

        for _ in v.data.extension_structure:

            _c = [_.get(x, []) for x in fields]

            for i in range(0, len(fields)):
                _k = key_fmt % fields[i]
                _v = DELIMITER.join(_c[0:i+1])

                if _v:
                    rv[_k].append(_v)

                rv[_k] = list(set(rv[_k]))

        return rv
