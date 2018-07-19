from decimal import Decimal
from zope.schema.interfaces import WrongType
from zope import schema

import json

from agsci.person.content.person import IProjectProgramTeamRowSchema

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
    complex_fields = ['project_program_team_percent',]

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

    def updateComplexFields(self, context, v):

        updated = False

        # Project/Program Team and Percent
        if v.data.project_program_team_percent:

            # Validate input data
            if not isinstance(v.data.project_program_team_percent, list):
                raise TypeError('project_program_team_percent is not an array')

            else:
                for i in v.data.project_program_team_percent:

                    if not isinstance(i, dict):
                        raise TypeError('project_program_team_percent item is not an associative array')
                    else:
                        # Validate incoming data structure against
                        # IProjectProgramTeamRowSchema

                        # Check for extra keys
                        input_keys = set(i.keys())
                        expected_keys = set(IProjectProgramTeamRowSchema.names())

                        extra_keys = list(input_keys - expected_keys)

                        if extra_keys:
                            raise ValueError('project_program_team_percent has extra keys %s' % repr(extra_keys))

                        # Check for valid data types
                        for (field_name, field) in IProjectProgramTeamRowSchema.namesAndDescriptions():

                            if i.has_key(field_name):

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

                                except WrongType, e:
                                    raise ValueError("Wrong type for %s: expected %s, not %s" % (field_name, e.args[1].__name__, e.args[0].__class__.__name__))

                                except:
                                    raise ValueError("Error with %s" % field_name)

            # Set project_program_team_percent if the new value is different
            if not self.compare_complex(
                context.project_program_team_percent,
                v.data.project_program_team_percent
            ):
                context.project_program_team_percent = v.data.project_program_team_percent
                updated = True

        return updated
