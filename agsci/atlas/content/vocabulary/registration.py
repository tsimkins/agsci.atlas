from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.component import getAdapters
from zope.interface import implements

from agsci.atlas.interfaces import IRegistrationFieldset
from agsci.atlas.utilities import ploneify

from ..adapters import EventDataAdapter
from ..event.group import IEventGroup

def tokenify(v):
    return ploneify(v).replace('-', '_')

# States and Countries for address fields

state_values = [
    u'Alabama', u'Alaska', u'Arizona', u'Arkansas', u'California', u'Colorado',
    u'Connecticut', u'Delaware', u'District Of Columbia', u'Florida', u'Georgia',
    u'Hawaii', u'Idaho', u'Illinois', u'Indiana', u'Iowa', u'Kansas', u'Kentucky',
    u'Louisiana', u'Maine', u'Maryland', u'Massachusetts', u'Michigan', u'Minnesota',
    u'Mississippi', u'Missouri', u'Montana', u'Nebraska', u'Nevada', u'New Hampshire',
    u'New Jersey', u'New Mexico', u'New York', u'North Carolina', u'North Dakota',
    u'Ohio', u'Oklahoma', u'Oregon', u'Pennsylvania', u'Rhode Island',
    u'South Carolina', u'South Dakota', u'Tennessee', u'Texas', u'Utah', u'Vermont',
    u'Virginia', u'Washington', u'West Virginia', u'Wisconsin', u'Wyoming',
    u'Puerto Rico', u'Virgin Island', u'Northern Mariana Islands', u'Guam',
    u'American Samoa', u'Palau',
]

country_values = [
    u'United States', u'Afghanistan', u'Albania', u'Algeria',
    u'American Samoa', u'Andorra', u'Angola', u'Anguilla', u'Antarctica',
    u'Antigua and Barbuda', u'Argentina', u'Armenia', u'Aruba',
    u'Australia', u'Austria', u'Azerbaijan', u'Bahamas', u'Bahrain',
    u'Bangladesh', u'Barbados', u'Belarus', u'Belgium', u'Belize',
    u'Benin', u'Bermuda', u'Bhutan', u'Bolivia', u'Bosnia and Herzegovina',
    u'Botswana', u'Bouvet Island', u'Brazil', u'British Indian Ocean Territory',
    u'Brunei', u'Bulgaria', u'Burkina Faso', u'Burundi', u'Cambodia',
    u'Cameroon', u'Canada', u'Cape Verde', u'Cayman Islands',
    u'Central African Republic', u'Chad', u'Chile', u'China',
    u'Christmas Island', u'Cocos ( Keeling ) Islands', u'Colombia',
    u'Comoros', u'Congo', u'Cook Islands', u'Costa Rica', u"C\xf4te d ' Ivoire",
    u'Croatia ( Hrvatska )', u'Cuba', u'Cyprus', u'Czech Republic',
    u'Congo ( DRC )', u'Denmark', u'Djibouti', u'Dominica', u'Dominican Republic',
    u'East Timor', u'Ecuador', u'Egypt', u'El Salvador', u'Equatorial Guinea',
    u'Eritrea', u'Estonia', u'Ethiopia', u'Falkland Islands ( Islas Malvinas )',
    u'Faroe Islands', u'Fiji Islands', u'Finland', u'France',
    u'French Guiana', u'French Polynesia', u'French Southern and Antarctic Lands',
    u'Gabon', u'Gambia', u'Georgia', u'Germany', u'Ghana', u'Gibraltar',
    u'Greece', u'Greenland', u'Grenada', u'Guadeloupe', u'Guam',
    u'Guatemala', u'Guinea', u'Guinea-Bissau', u'Guyana', u'Haiti',
    u'Heard Island and McDonald Islands', u'Honduras', u'Hong Kong SAR',
    u'Hungary', u'Iceland', u'India', u'Indonesia', u'Iran',
    u'Iraq', u'Ireland', u'Israel', u'Italy', u'Jamaica', u'Japan',
    u'Jordan', u'Kazakhstan', u'Kenya', u'Kiribati', u'Korea',
    u'Kuwait', u'Kyrgyzstan', u'Laos', u'Latvia', u'Lebanon',
    u'Lesotho', u'Liberia', u'Libya', u'Liechtenstein', u'Lithuania',
    u'Luxembourg', u'Macao SAR', u'Macedonia, Former Yugoslav Republic of',
    u'Madagascar', u'Malawi', u'Malaysia', u'Maldives', u'Mali',
    u'Malta', u'Marshall Islands', u'Martinique', u'Mauritania',
    u'Mauritius', u'Mayotte', u'Mexico', u'Micronesia', u'Moldova',
    u'Monaco', u'Mongolia', u'Montserrat', u'Morocco', u'Mozambique',
    u'Myanmar', u'Namibia', u'Nauru', u'Nepal', u'Netherlands',
    u'Netherlands Antilles', u'New Caledonia', u'New Zealand',
    u'Nicaragua', u'Niger', u'Nigeria', u'Niue', u'Norfolk Island',
    u'North Korea', u'Northern Mariana Islands', u'Norway', u'Oman',
    u'Pakistan', u'Palau', u'Panama', u'Papua New Guinea', u'Paraguay',
    u'Peru', u'Philippines', u'Pitcairn Islands', u'Poland',
    u'Portugal', u'Puerto Rico', u'Qatar', u'Reunion', u'Romania',
    u'Russia', u'Rwanda', u'Samoa', u'San Marino',
    u'S\xe3o Tom\xe9 and Pr\xecncipe',
    u'Saudi Arabia', u'Senegal', u'Serbia and Montenegro', u'Seychelles',
    u'Sierra Leone', u'Singapore', u'Slovakia', u'Slovenia',
    u'Solomon Islands', u'Somalia', u'South Africa',
    u'South Georgia and the South Sandwich Islands',
    u'Spain', u'Sri Lanka', u'St. Helena', u'St. Kitts and Nevis',
    u'St. Lucia', u'St. Pierre and Miquelon', u'St. Vincent and the Grenadines',
    u'Sudan', u'Suriname', u'Svalbard and Jan Mayen', u'Swaziland',
    u'Sweden', u'Switzerland', u'Syria', u'Taiwan', u'Tajikistan',
    u'Tanzania', u'Thailand', u'Togo', u'Tokelau', u'Tonga',
    u'Trinidad and Tobago', u'Tunisia', u'Turkey', u'Turkmenistan',
    u'Turks and Caicos Islands', u'Tuvalu', u'Uganda', u'Ukraine',
    u'United Arab Emirates', u'United Kingdom',
    u'United States Minor Outlying Islands',
    u'Uruguay', u'Uzbekistan', u'Vanuatu', u'Vatican City', u'Venezuela',
    u'Viet Nam', u'Virgin Islands ( British )', u'Virgin Islands',
    u'Wallis and Futuna', u'Yemen', u'Zambia', u'Zimbabwe'
]

gender_values = [
    'Male',
    'Female',
    'Prefer not to answer'
]

age_values = [
    'Under 18 years',
    '18 years or older'
]

ethnicity_values = [
    'Hispanic/Latino',
    'Non-Hispanic/Latino',
    'Prefer not to answer'
]

race_values = [
    'American Indian/Alaska Native',
    'Asian',
    'Black/African American',
    'Pacific Islander/Native Hawaiian',
    'White',
    'Two or more races',
    'Some other race',
    'Prefer not to answer'
]

class RegistrationField(object):

    attrs = {
        'type' : 'field',
        'token' : '',
        'title' : '',
        'is_require' : False,
        'options' : [],
        'is_visitor_option' : True,
    }

    optional_attrs = [
        'max_characters',
    ]

    def __init__(self, **kwargs):

        self.data = {}

        # Iterate through the default attrs, and if we override them, set the
        # value on the data dict.  If not, set the default.
        for (k,v) in self.attrs.iteritems():

            value = kwargs.get(k, v)

            self.data[k] = value

        for k in self.optional_attrs:
            if kwargs.has_key(k):
                value = kwargs.get(k)
                self.data[k] = value

        # Add title/token to options
        for i in range(0, len(self.data['options'])):
            v = self.data['options'][i]

            # If we passed in a raw string, convert it to a dict with
            # title/token as keys.  This lets us override the autogenerated
            # token if we change the title.
            if isinstance(v, (str, unicode)):
                self.data['options'][i] = {
                    'title' : v,
                    'token' : tokenify(v)
                 }

        # Remove empty fields
        for k in ('options',):
            if not self.data[k]:
                del self.data[k]

        # Initialize sort_order with 0
        self.data['sort_order'] = 0

        # Set token: Explicit, type (if not 'field', normalized title)
        if not self.data['token']:
            if self.data['type'] in ('field', 'checkbox', 'drop_down', 'radio', 'multiple', 'date'):
                self.data['token'] = tokenify(self.data['title'])
            else:
                self.data['token'] = self.data['type']


class BaseRegistrationFields(object):

    label = "Base"
    sort_order = 9999
    required = True

    fields = []

    def __init__(self, context):
        self.context = context

    def getFieldType(self, field):
        return 'field'

    def getFields(self):
        if hasattr(self, 'fields'):
            return [self.getFieldData(x) for x in self.fields]

        return []

    def getFieldData(self, field=None):
        return dict(getattr(field, 'data', {}))

class BasicRegistrationFields(BaseRegistrationFields):

    label = "Basic"
    sort_order = 10

    @property
    def fields(self):
        return [
            RegistrationField(
                type='firstname',
                title='First Name',
            ),
            RegistrationField(
                type='lastname',
                title='Last Name',
            ),
            RegistrationField(
                type='email',
                title='Email',
            ),
            RegistrationField(
                type='primary_phone',
                title='Primary Phone',
            ),
            RegistrationField(
                type='primary_phone_type',
                title='Primary Phone Type',
                options=['Home', 'Work', 'Mobile'],
            ),
        ]

class BusinessRegistrationFields(BaseRegistrationFields):

    label = "Business"
    sort_order = 20
    required = False

    @property
    def fields(self):
        return [
            RegistrationField(
                title='Address Type',
                type="drop_down",
                options=['Home', 'Work',],
            ),
            RegistrationField(
                title='Company Name',
            ),
            RegistrationField(
                title='Address Line 1',
            ),
            RegistrationField(
                title='Address Line 2',
            ),
            RegistrationField(
                title='City',
            ),
            RegistrationField(
                title='State/Province',
                type="drop_down",
                options=state_values,
            ),
            RegistrationField(
                title='Postal Code',
            ),
            RegistrationField(
                title='Country',
                type="drop_down",
                options=country_values,
            ),
        ]

class DemographicRegistrationFields(BaseRegistrationFields):

    label = "Demographics"
    sort_order = 40

    @property
    def fields(self):
        return [

            RegistrationField(
                title="Gender",
                token="gender",
                type="drop_down",
                is_require=True,
                is_visitor_option=True,
                options=gender_values,
            ),

            RegistrationField(
                title="Age",
                token="age",
                type="drop_down",
                is_require=True,
                is_visitor_option=True,
                options=age_values,
            ),

            RegistrationField(
                title="Ethnicity",
                token="ethnicity",
                type="drop_down",
                is_require=True,
                is_visitor_option=True,
                options=ethnicity_values,
            ),

            RegistrationField(
                title="Race",
                token="race",
                type="drop_down",
                is_require=True,
                is_visitor_option=True,
                options=race_values,
            ),

        ]

class AccessibilityRegistrationFields(BaseRegistrationFields):

    label = "Accessibility"
    sort_order = 50

    @property
    def fields(self):
        return [
            RegistrationField(
                token="accessibility",
                title='Do you require assistance?',
                options=['Audio', 'Visual', 'Mobile'],
                type='checkbox',
            )
        ]

class Act48CreditsRegistrationFields(BaseRegistrationFields):

    label = "Act 48 Credits"
    sort_order = 30
    required = False

    @property
    def fields(self):
        return [
            RegistrationField(
                type='field',
                title='PDE Professional Personnel ID (PPID)',
            ),
            RegistrationField(
                token="consent_to_report",
                type='checkbox',
                title="""By providing your PPID and checking this box, you are confirming that you are an educator in Pennsylvania seeking to earn Act 48 credits, and are authorizing The Pennsylvania State University (PSU) to release your educational record information to Pennsylvania Department of Education (PDE) for Act 48 purposes only.""",
                options=[{
                    'token' : u'yes',
                    'title' : u'Yes, I approve PSU to release my educational record information for Act 48 purposes'
                }],
            ),
        ]

class PesticideEducationCreditsRegistrationFields(BaseRegistrationFields):

    label = "Pesticide Education Credits"
    sort_order = 30
    required = False

    @property
    def fields(self):
        return [
            RegistrationField(
                type='date',
                title='Date of Birth',
            ),
            RegistrationField(
                type='field',
                title='Pennsylvania Pesticide License #',
            ),
            RegistrationField(
                token="acknowledgement_statement",
                type='radio',
                title="""I acknowledge that a complete license number must be included for credit to be granted, and I authorize Penn State Extension to submit my information and earned credit(s) to Pennsylvania Department of Agriculture upon successful completion of the course.""",
                options=[u'Yes', u'No'],
            ),
        ]

class SLFOnlineCourseRegistrationFields(BaseRegistrationFields):

    label = "Spotted Lanternfly Online Course"
    sort_order = 30
    required = False

    @property
    def fields(self):
        return [

            RegistrationField(
                title="Legal Name of Company or Agency",
                token="legal_company_name",
                type="field",
                is_require=True,
                is_visitor_option=True,
            ),

            RegistrationField(
                title='Address Line 1',
                is_require=True,
            ),

            RegistrationField(
                title='Address Line 2',
            ),

            RegistrationField(
                title='City',
                is_require=True,
            ),

            RegistrationField(
                title='State',
                type="drop_down",
                options=state_values,
                is_require=True,
            ),

            RegistrationField(
                title='Postal Code',
                is_require=True,
            ),

            RegistrationField(
                title="Number of Company Vehicles Requiring Permits",
                token="vehicle_permit_qty",
                type="field",
                max_characters=4,
                is_require=True,
                is_visitor_option=True,
            ),

            RegistrationField(
                title="The person taking this exam, whose name appears on this registration, verifies to the Commonwealth of Pennsylvania and Department of Agriculture, that s/he has the authority to execute a permit and thereby be bound to its terms thereof. The person agrees to abide by the terms of this permit, defined in Pennsylvania's Spotted Lanternfly Order of Quarantine. This includes training of employees who handle regulated articles.",
                token="acknowledgement_statement",
                type="checkbox",
                is_require=True,
                is_visitor_option=True,
                options=['Yes', ]
            ),

        ]


class SAFOnlineCourseRegistrationFields(BaseRegistrationFields):

    label = "Society for American Foresters"
    sort_order = 30
    required = False

    @property
    def fields(self):
        return [

            RegistrationField(
                title="Society for American Foresters (SAF) Certified?",
                token="saf_certified",
                type="radio",
                is_require=False,
                is_visitor_option=True,
                options=[u'Yes', u'No'],
            ),

            RegistrationField(
                title="Society for American Foresters (SAF) Member?",
                token="saf_member",
                type="radio",
                is_require=False,
                is_visitor_option=True,
                options=[u'Yes', u'No'],
            ),

            RegistrationField(
                title="State License / Registration Number",
                token="state_license_number",
                type="field",
                is_require=False,
                is_visitor_option=True,
            ),
        ]


class RegistrationFieldsetsVocabulary(object):

    implements(IVocabularyFactory)

    # Returns a list of fieldsets sorted in order
    def getRegistrationFieldsets(self, context):

        fieldsets = [x for x in getAdapters((context,), IRegistrationFieldset)]

        fieldsets.sort(key=lambda x: x[1].sort_order)

        return fieldsets

    def getDefaults(self, context):
        return [x[0] for x in self.getRegistrationFieldsets(context) if x[1].required]

    def __call__(self, context):

        # Check the request to make sure this is not being triggered by an import
        try:
            request_url = context.REQUEST.getURL()
        except:
            # Can't get the URL, don't do anything
            pass
        else:
            # If the URL contains '++add++', context is actually the container.
            # Do a check to see if IEventGroup is provided by the parent.
            if '++add++' in request_url:
                if IEventGroup.providedBy(context):
                    return SimpleVocabulary([])

        # If this context has a parent that's an IEventGroup, return an empty
        # vocabulary
        if EventDataAdapter(context).getParentId():
            return SimpleVocabulary([])

        # Initialize items list
        items = []

        # Iterate through fieldsets, and append to items
        for (name, fieldset) in self.getRegistrationFieldsets(context):
            items.append(SimpleTerm(name, title=fieldset.label))

        # Return a SimpleVocabulary of these items
        return SimpleVocabulary(items)

RegistrationFieldsetsVocabularyFactory = RegistrationFieldsetsVocabulary()