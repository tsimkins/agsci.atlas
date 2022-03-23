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

# Short Countries

short_country_values = [
    u'United States', u'Canada',
]

lead_source_values = [
    u'Penn State Extension Website',
    u'Penn State Extension Email',
    u'Penn State Event',
    u'Special Event (Farm show, fair, industry tradeshow or conference)',
    u'Postcard or Mail',
    u'Internet Search (Google, Bing, etc.)',
    {
        "title": "Word of Mouth (Friend, Coworker, Spouse, etc.)",
        "token": "word_of_mouth"
    },
    {
        "title": "Social Media (Facebook, Twitter, etc.)",
        "token": "social_media"
    },
    u'Newspaper or Magazine',
    u'Radio',
    {
        "title": "Not sure",
        "token": "i_dont_recall"
    },
    u'Other, specify below',
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
    default = False

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

class MarketingRegistrationFields(BaseRegistrationFields):

    label = "Marketing"
    sort_order = 45
    default = True

    @property
    def fields(self):
        return [

            RegistrationField(
                title="How did you hear about this event / online course?",
                token="lead_source",
                type="drop_down",
                is_require=False,
                is_visitor_option=True,
                options=lead_source_values,
            ),

            RegistrationField(
                type='field',
                token='lead_source_other',
                title='If you selected other, please specify below.',
                is_require=False,
            ),
        ]

class AccessibilityRegistrationFields(BaseRegistrationFields):

    label = "Accessibility"
    sort_order = 50
    default = True

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

class SLFOnlineCourseRegistrationFieldsBase(BaseRegistrationFields):

    label = "Spotted Lanternfly Online Course"
    sort_order = 30
    vehicle_permit_qty = True

    @property
    def fields(self):
        _ = [

            RegistrationField(
                title="Legal Company Name",
                token="company_name",
                type="field",
                is_require=True,
                is_visitor_option=True,
            ),

            RegistrationField(
                title='Country',
                type="drop_down",
                options=short_country_values,
                is_require=True,
            ),

        ]

        # Only add the permit quantity if required.
        if self.vehicle_permit_qty:

            _.append(
                RegistrationField(
                    title="Number of Company Vehicles",
                    token="vehicle_permit_qty",
                    type="field",
                    max_characters=4,
                    is_require=True,
                    is_visitor_option=True,
                ),
            )

        return _

class SLFOnlineCourseRegistrationFields(SLFOnlineCourseRegistrationFieldsBase):

    label = "Spotted Lanternfly Online Course (PA)"

    @property
    def fields(self):

        _ = super(SLFOnlineCourseRegistrationFields, self).fields

        _.append(
            RegistrationField(
                title="The person taking this exam, whose name appears on this registration, verifies to the Commonwealth of Pennsylvania and Department of Agriculture, that s/he has the authority to execute a permit and thereby be bound to its terms thereof. The person agrees to abide by the terms of this permit, defined in Pennsylvania's Spotted Lanternfly Order of Quarantine. This includes training of employees who handle regulated articles.",
                type="checkbox",
                is_require=True,
                is_visitor_option=True,
                options=['Yes', ]
            ),
        )

        return _

class SLFOnlineCourseRegistrationFields_NJ(SLFOnlineCourseRegistrationFieldsBase):

    label = "Spotted Lanternfly Online Course (NJ)"

    @property
    def fields(self):
        _ = super(SLFOnlineCourseRegistrationFields_NJ, self).fields

        _.append(
            RegistrationField(
                title="The person taking this exam, whose name appears on this registration, verifies to the State of New Jersey Department of Agriculture, that s/he has the authority to execute a permit and thereby be bound to its terms thereof. The person agrees to abide by the terms of this permit, defined in New Jersey's Spotted Lanternfly Order of Quarantine. This includes training of employees who handle regulated articles.",
                token="acknowledgement_statement",
                type="checkbox",
                is_require=True,
                is_visitor_option=True,
                options=['Yes', ]
            ),
        )

        return _

class SLFOnlineCourseRegistrationFields_MD(SLFOnlineCourseRegistrationFieldsBase):

    label = "Spotted Lanternfly Online Course (MD)"
    vehicle_permit_qty = False

    @property
    def fields(self):
        _ = super(SLFOnlineCourseRegistrationFields_MD, self).fields

        _.append(
            RegistrationField(
                title="The person taking this exam, whose name appears on this registration, verifies to the State of Maryland, the Maryland Department of Agriculture, that s/he has the authority to execute the terms of the state permit, or is acting under a person with this authority. The person agrees to abide by the terms of the permit, defined in Maryland's Spotted Lanternfly Order of Quarantine. This includes training of employees who handle regulated articles.",
                token="acknowledgement_statement",
                type="checkbox",
                is_require=True,
                is_visitor_option=True,
                options=['Yes', ]
            ),
        )

        return _

class IRSOnlineCourseRegistrationFields(BaseRegistrationFields):

    label = "IRS Tax Information"
    sort_order = 25

    @property
    def fields(self):
        return [

            RegistrationField(
                title="Enter your Preparer Tax Identification Number (PTIN) to earn continuing education credits from the IRS",
                token="irs_preparer_tax_identification_number",
                type="field",
                is_require=False,
                is_visitor_option=True,
            ),
        ]

class SAFOnlineCourseRegistrationFields(BaseRegistrationFields):

    label = "Society for American Foresters"
    sort_order = 30

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
                title="Enter your SAF State License / Registration Number to earn continuing education credits from the Society of American Foresters",
                token="saf_state_license_number",
                type="field",
                is_require=False,
                is_visitor_option=True,
            ),
        ]


class ContactTracingRegistrationFields(BaseRegistrationFields):

    label = "Contact Tracing"
    sort_order = 30

    @property
    def fields(self):
        return [
            RegistrationField(
                title='How are you affiliated with Penn State?',
                type="checkbox",
                options=[
                    'Faculty',
                    'Staff',
                    'Student',
                    'None of the above',
                ],
            ),
            RegistrationField(
                title='Registered Nurse (RN) License Number',
            ),
            RegistrationField(
                title="""By providing your RN license number and checking this box, you are consenting to earn 3.0 contact hours for successfully completing this course. Note: Only registered nurses who complete the course and achieve a passing score of at least 80% are eligible for the contact hours.""",
                token="registered_nurse_contact_hours_acknowledgement",
                type="checkbox",
                options=[{
                    'token' : u'yes',
                    'title' : u'Yes, I consent to earn 3.0 contact hours upon successful completion of the course.'
                }],
            ),
        ]

class SwineHealthMonitoringRegistrationFields(BaseRegistrationFields):

    label = "Swine Health Monitoring"
    sort_order = 30

    @property
    def fields(self):
        return [
            RegistrationField(
                token="acknowledgement_statement",
                type='radio',
                title="""I am at least 18-years-old and I have sufficient experience with swine to be able to recognize abnormalities with their appearance, health, and behavior.""",
                is_require=True,
                options=[u'Yes', u'No'],
            ),
        ]

class NSTMOPRegistrationFields(BaseRegistrationFields):

    label = "NSTMOP"
    sort_order = 30

    @property
    def fields(self):
        return [

            RegistrationField(
                title="Legal Company Name",
                token="company_name",
                type="field",
                is_require=True,
                is_visitor_option=True,
            ),

            RegistrationField(
                token="acknowledgement_statement",
                type='radio',
                title="""I confirm that I am at least 18-years-old and eligible to take the National Safe Tractor and Machinery Operation Program (NSTMOP) Instructor Training course.""",
                is_require=True,
                options=[u'Yes', u'No'],
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
        return [x[0] for x in self.getRegistrationFieldsets(context) if x[1].default]

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