from decimal import Decimal
from zope.schema.interfaces import WrongType
from zope import schema

import json

from agsci.person.content.person import IProjectProgramTeamRowSchema, \
                                        IProjectPercentRowSchema

from . import SyncContentView

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return '%0.8f' % o
        return json.JSONEncoder.default(self, o)

# View that accepts a POST of JSON data, and updates a Person in Plone
# Initially this is just the financial information
class SyncPersonView(SyncContentView):

    # Complex fields
    complex_fields = ['project_program_team_percent', 'program_percent']

    # Cannot create people
    can_create = False

    # Quick and dirty comparison by converting values to json string and checking
    # for equality
    def compare_complex(self, v1, v2):

        def to_json(_):

            if isinstance(_, list):
                return json.dumps(sorted(_), sort_keys=True, cls=CustomJSONEncoder)

            return json.dumps(_, cls=CustomJSONEncoder)

        return to_json(v1) == to_json(v2)

    # Don't create people with the API
    def createObject(self, context, v):
        pass

    def do_update_complex_field(self, context, v, f_name, f_interface):

        updated = False

        f_value = getattr(v.data, f_name, None)

        # Validate the field type
        if f_value:

            # Validate input data
            if not isinstance(f_value, list):
                raise TypeError('%s is not an array' % f_name)

            else:
                for i in f_value:

                    if not isinstance(i, dict):
                        raise TypeError('%s item is not an associative array' % f_name)
                    else:
                        # Validate incoming data structure against schema

                        # Check for extra keys
                        input_keys = set(i.keys())
                        expected_keys = set(f_interface.names())

                        extra_keys = list(input_keys - expected_keys)

                        if extra_keys:
                            raise ValueError('%s has extra keys %s' % (f_name, repr(extra_keys)))

                        # Check for valid data types
                        for (field_name, field) in f_interface.namesAndDescriptions():

                            if field_name in i:

                                # Strip whitespace from strings
                                if isinstance(i[field_name], (str, unicode)):
                                    i[field_name] = i[field_name].strip()

                                # If the field type is a decimal, and a float or
                                # int are provided, convert to Decimal
                                if isinstance(field, schema.Decimal):

                                    if isinstance(i[field_name], (float, int, str, unicode)):
                                        i[field_name] = Decimal(i[field_name])

                                # Run the validation for the schema field against
                                # the incoming data
                                try:
                                    field.validate(i[field_name])

                                except WrongType as e:
                                    raise ValueError("Wrong type for %s: expected %s, not %s" % (field_name, e.args[1].__name__, e.args[0].__class__.__name__))

                                except:
                                    raise ValueError("Error with %s" % field_name)

            # Set field if the new value is different
            if not self.compare_complex(
                getattr(context, f_name, []),
                f_value
            ):
                setattr(context, f_name, f_value)
                updated = True

        return updated

    def updateComplexFields(self, context, v):

        updated = []

        for (f_name, f_interface) in [
            ('project_program_team_percent', IProjectProgramTeamRowSchema),
            ('project_percent', IProjectPercentRowSchema),
        ]:
            updated.append(
                self.do_update_complex_field(context, v, f_name, f_interface)
            )

        return any(updated)
