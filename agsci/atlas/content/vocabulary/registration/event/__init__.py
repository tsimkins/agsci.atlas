from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from .. import BaseRegistrationFields as _BaseRegistrationFields
from .. import RegistrationField as _RegistrationField
from .. import RegistrationFieldsetsVocabulary as _RegistrationFieldsetsVocabulary
from .. import lead_source_values

from agsci.atlas.content.adapters import EventDataAdapter, EventRegistrationFieldsetDataAdapter
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.content.vocabulary import KeyValueVocabulary
from agsci.atlas.interfaces import IEventRegistrationFieldset

class RegistrationField(_RegistrationField):

    attrs = {
        'type' : 'field',
        'token' : '',
        'title' : '',
        'is_require' : False,
        'options' : [],
        'is_visitor_option' : True,
        'step' : '',
        'step_label' : '',
        'registrant_types' : []
    }


class BaseRegistrationFields(_BaseRegistrationFields):

    step = 99
    default = False

    registrant_types = []

    @property
    def all_registrant_types(self):
        adapted = EventRegistrationFieldsetDataAdapter(self.context)
        return [x.value for x in adapted.all_registrant_types]

    @property
    def selected_registrant_types(self):
        _ = getattr(self.context.aq_base, 'registrant_types', [])
        if _:
            return [x for x in _ if x in self.all_registrant_types]
        return []

    def getRegistrantTypes(self):
        selected_registrant_types = self.selected_registrant_types

        if self.registrant_types:
            return [x for x in self.registrant_types if x in selected_registrant_types]

        return selected_registrant_types

    def getFieldData(self, field=None):
        _ = dict(getattr(field, 'data', {}))

        if 'registrant_types' in _ and _['registrant_types']:
            _['registrant_types'] = [x for x in _['registrant_types'] if x in self.all_registrant_types]
        else:
            _['registrant_types'] = self.getRegistrantTypes()

        return _

class MinimalRegistrationFields(BaseRegistrationFields):

    label = "Minimal"
    sort_order = 10
    step = 1
    default = True

    fields= [
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
    ]

class PennStateRegistrationFields(BaseRegistrationFields):

    label = "Penn State Information"
    sort_order = 15
    step = 2
    default = False

    fields= [
        RegistrationField(
            title="Please indicate your current Penn State affiliation status.",
            type="radio",
            token='penn_state_affiliation_status',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Penn State Employee',
                'Dependent of Penn State Employee',
                'Penn State Retiree',
            ],
            registrant_types=[
                'penn_state_employee_dependent_retiree',
            ]
        ),
    ]

class TermsAndConditionsRegistrationFields(BaseRegistrationFields):

    label = "Terms and Conditions"
    step = 2
    default = True
    sort_order = 20

    fields= [
        RegistrationField(
            title="You must be 18 years of age or older to be a registrant on this website for this event. If you have questions, please contact Customer Service at 1-877-345-0691.",
            token="age_acknowledgement",
            type="checkbox",
            is_require=True,
            is_visitor_option=True,
            options=[
                'I understand and agree',
            ]
        ),
    ]

class DietaryRegistrationFields(BaseRegistrationFields):

    label = "Dietary"
    step = 2
    sort_order = 30

    fields = [
        RegistrationField(
            title="Please indicate if you have any dietary restrictions.",
            type="checkbox",
            token='dietary',
            is_require=True,
            is_visitor_option=True,
            options=[
                'None',
                'Diabetic',
                'Gluten-free',
                'Kosher',
                'Vegetarian',
                'Other',
            ]
        ),
        RegistrationField(
            title='If you selected other, please specify below.',
            type='field',
            token='dietary_other',
            is_require=False,
        ),
        RegistrationField(
            title="Would you like an attendee cookie?",
            type="radio",
            token='attendee_cookie',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Yes',
                'No',
            ],
            registrant_types = [
                'general_attendee',
            ]
        ),
        RegistrationField(
            title="Would you like a speaker cookie?",
            type="radio",
            token='speaker_cookie',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Yes',
                'No',
            ],
            registrant_types = [
                'speaker_instructor_and_or_presenter',
            ]
        ),
        RegistrationField(
            title="What color would you like your cookie to be?",
            type="radio",
            token='penn_state_cookie',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Blue',
                'White',
                'Blue and White',
            ],
            registrant_types = [
                'penn_state_employee_dependent_retiree',
            ]
        ),

    ]

class AccommodationsInPersonRegistrationFields(BaseRegistrationFields):

    label = "Accommodations - In-Person"
    step = 2
    sort_order = 40

    fields = [
        RegistrationField(
            title='Penn State encourages persons with disabilities to participate in its programs and activities. Please let us know if you anticipate needing any specific aids or services to participate in this event. Submitting requests at least 2 business days in advance will provide the best opportunity to have your request filled.',
            type='checkbox',
            token="accommodations_in_person",
            options=[
                'None',
                'Audio',
                'Visual',
                'Mobile',
                'Other',
            ],
        ),
        RegistrationField(
            title='If you selected Other, please specify below. ',
            type='field',
            token='accommodations_in_person_other',
            is_require=False,
        ),
    ]

class AccommodationsVirtualRegistrationFields(BaseRegistrationFields):

    label = "Accommodations - Virtual"
    step = 2
    sort_order = 40

    fields = [
        RegistrationField(
            title='Penn State encourages persons with disabilities to participate in its programs and activities. Please let us know if you anticipate needing any specific aids or services to participate in this event. Submitting requests at least 2 business days in advance will provide the best opportunity to have your request filled. ',
            type='checkbox',
            token="accommodations_virtual",
            options=[
                'None',
                'Audio - Live-Person Closed Captioning ',
                'Audio - Machine-Generated Closed Captioning',
                'Audio - Other',
                'Other',
            ],
        ),
        RegistrationField(
            title='If you selected Other, please let us know what would be most helpful.',
            type='field',
            token='accommodations_virtual_other',
            is_require=False,
        ),
    ]

class MarketingRegistrationFields(BaseRegistrationFields):

    label = "Marketing"
    step = 3
    default = True
    sort_order = 60

    fields = [
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

class ServSafeRegistrationFields(BaseRegistrationFields):

    label = "ServSafe"
    sort_order = 100

    fields = [
        RegistrationField(
            title="Choose the language for your textbook.",
            token="servsafe_textbook_language",
            type="drop_down",
            is_require=False,
            is_visitor_option=True,
            options=[
                'English Book',
                'Spanish Book',
                'Chinese Book',
                'Korean Book',
            ]
        ),
        RegistrationField(
            title="Choose the language for your exam.",
            token="servsafe_exam_language",
            type="drop_down",
            is_require=False,
            is_visitor_option=True,
            options=[
                'English Exam',
                'Large Print English Exam',
                'Spanish / English Bilingual Exam',
                'Chinese / English Bilingual Exam',
                'French-Canadian / English Bilingual Exam',
                'Korean / English Bilingual Exam',
                'Japanese / English Bilingual Exam',
            ]
        ),
    ]

class UrbanForestryRegistrationFields(BaseRegistrationFields):

    label = "Urban Forestry"
    sort_order = 100

    fields = [
        RegistrationField(
            token="urban_forestry_municipality",
            type='radio',
            title="""Do you represent a municipality – paid or volunteer? (Ex.: Elected Official, Tree Commission, etc.)""",
            options=[u'Yes', u'No'],
            is_require=True,
        ),
        RegistrationField(
            type='field',
            title='If Yes, Name of municipality',
            token="urban_forestry_municipality_name",
            is_require=True,
        ),
        RegistrationField(
            title="If Yes, which category best describes your affiliation?",
            token="urban_forestry_municipality_affiliation",
            type="drop_down",
            is_require=False,
            is_visitor_option=True,
            options=[
                'Elected Official',
                'Planning Commission',
                'Tree Commission',
                'Consultant',
                'Employee',
                'Other',
            ]
        ),
    ]

class DiningWithDiabetesRegistrationFields(BaseRegistrationFields):

    label = "Dining with Diabetes"
    sort_order = 100

    fields = [
        RegistrationField(
            title="Date of Birth",
            type="date",
            token='dwd_amerihealth_caritas_dob',
            is_require=True,
            is_visitor_option=True,
            registrant_types=[
                'amerihealth_member',
            ]
        ),
        RegistrationField(
            title='Penn State Extension is in partnership with AmeriHealth Caritas Pennsylvania to sponsor Dining with Diabetes registrations for AmeriHealth Caritas Pennsylvania members. To qualify for a free sponsorship of this event, your registration details, including contact information and date of birth, will be provided to AmeriHealth Caritas Pennsylvania to verify your eligibility.',
            type='checkbox',
            token="dwd_amerihealth_caritas_acknowledgement",
            options=[
                'I understand and agree',
            ],
            registrant_types=[
                'amerihealth_member',
            ]
        ),
        RegistrationField(
            title="Please indicate if you participate in any of the following programs. Check all that apply.",
            type="checkbox",
            token='dwd_participate_programs',
            is_require=True,
            is_visitor_option=True,
            options=[
                'PACE or PACEnet',
                'Medicate Premium Assistance Program',
                'Medicaid',
                'L.I.HEAP',
                "Farmer's Market Nutrition Program",
                'SNAP',
                'Free/Reduced Lunch Program for your dependent children',
                'Prefer not to answer',
                'I do not participate in any of these programs',
            ]
        ),
    ]


class LIFT812WeeksRegistrationFields(BaseRegistrationFields):

    label = "LIFT (8/12 Weeks)"
    sort_order = 100

    fields = [
        RegistrationField(
            title="When did you last participate in a LIFT program?",
            type="radio",
            token='lift812_last_participate',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Less than 6 months ago',
                'More than 6 months ago',
                'I am a new participant',
            ]
        ),
        RegistrationField(
            title="Please indicate if you participate in any of the following programs. Check all that apply.",
            type="checkbox",
            token='lift812_participate_programs',
            is_require=True,
            is_visitor_option=True,
            options=[
                'PACE or PACEnet',
                'Medicate Premium Assistance Program',
                'Medicaid',
                'L.I.HEAP',
                "Farmer's Market Nutrition Program",
                'SNAP',
                'Free/Reduced Lunch Program for your dependent children',
                'Prefer not to answer',
                'I do not participate in any of these programs',
            ]
        ),
    ]


class AgWorksWebinarRegistrationFields(BaseRegistrationFields):

    label = "AgWorks Webinar"
    sort_order = 100

    fields = [
        RegistrationField(
            title="Which of the following best describes your affiliation?",
            type="radio",
            token='agworks_affiliation',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Farm/Agribusiness',
                'Other',
            ]
        ),
        RegistrationField(
            title="Please indicate which of the following statements apply to your farm or agribusiness. You may select more than one,",
            type="checkbox",
            token='agworks_statements',
            is_require=True,
            is_visitor_option=True,
            options=[
                'The farm or agribusiness is a small to medium-sized operation with an average annual income of approximately $38 million or less',
                'The farm or agribusiness is located in Pennsylvania',
                'The farm or agribusiness is not government-owned',
                'The farm or agribusiness has fewer than 100 employees (including seasonal and year-round), or plans to hire at least one employee within the next 12 months',
                'I prefer not to answer',
                'I do not know',
                'Not applicable',
            ]
        ),
        RegistrationField(
            title="As part of the AgWorks grant, we are offering no-cost training and consultation services to qualifying farms and agribusinesses in Pennsylvania. Would you like to be contacted if you qualify for additional services?",
            type="radio",
            token='agworks_contact_additional_services',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Yes, please contact me',
                'No, do not contact me',
            ]
        ),
    ]


class WaterTestingRegistrationFields(BaseRegistrationFields):

    label = "Water Testing"
    sort_order = 100

    fields = [
        RegistrationField(
            title="I confirm that I use a private water supply as my primary source of drinking water.",
            type="checkbox",
            token='water_testing_primary_source',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Yes',
            ]
        ),
        RegistrationField(
            title="I confirm that I plan to participate in the free water testing provided by this program.",
            type="checkbox",
            token='water_testing_participate_testing',
            is_require=True,
            is_visitor_option=True,
            options=[
                'Yes',
            ]
        ),
    ]



class RegistrationFieldsetsVocabulary(_RegistrationFieldsetsVocabulary):

    interface = IEventRegistrationFieldset
    step = 99

    # Returns a list of fieldsets sorted in order
    def getRegistrationFieldsets(self, context):

        fieldsets = super(RegistrationFieldsetsVocabulary, self).getRegistrationFieldsets(context)

        return [x for x in fieldsets if getattr(x[1], 'step') == self.step]

class Step1RegistrationFieldsetsVocabulary(RegistrationFieldsetsVocabulary):
    step = 1
    label = f"Step 1: Contact Information"

class Step2RegistrationFieldsetsVocabulary(RegistrationFieldsetsVocabulary):
    step = 2
    label = f"Step 2: Acknowledgment and Accommodations"

class Step3RegistrationFieldsetsVocabulary(RegistrationFieldsetsVocabulary):
    step = 3
    label = f"Step 3: Marketing"

class Step99RegistrationFieldsetsVocabulary(RegistrationFieldsetsVocabulary):
    pass

Step1RegistrationFieldsetsVocabularyFactory = Step1RegistrationFieldsetsVocabulary()
Step2RegistrationFieldsetsVocabularyFactory = Step2RegistrationFieldsetsVocabulary()
Step3RegistrationFieldsetsVocabularyFactory = Step3RegistrationFieldsetsVocabulary()
Step99RegistrationFieldsetsVocabularyFactory = Step99RegistrationFieldsetsVocabulary()


class RegistrantTypeVocabulary(KeyValueVocabulary):

    items = [
        ('general_attendee', 'General Attendee'),
        ('speaker_instructor_and_or_presenter', 'Speaker, Instructor, and/or Presenter'),
        ('penn_state_employee_dependent_retiree', 'Penn State Employee/Dependent/Retiree'),
        ('amerihealth_member', 'AmeriHealth Member'),
        ('credit_seeking_attendee', 'Credit Seeking Attendee'),
        ('non_credit_seeking_attendee', 'Non-Credit Seeking Attendee'),
        ('sponsor', 'Sponsor'),
        ('bronze_sponsor', 'Bronze Sponsor'),
        ('silver_sponsor', 'Silver Sponsor'),
        ('gold_sponsor', 'Gold Sponsor'),
        ('platinum_sponsor', 'Platinum Sponsor'),
        ('student_attendee', 'Student Attendee'),
        ('full_day_attendee', 'Full Day Attendee'),
        ('morning_only_attendee', 'Morning Only Attendee'),
        ('afternoon_only_attendee', 'Afternoon Only Attendee'),
    ]

RegistrantTypeVocabularyFactory = RegistrantTypeVocabulary()
