from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.component import getAdapters
from zope.interface import implements

from agsci.atlas.interfaces import IRegistrationFieldset

from ..adapters import EventDataAdapter
from ..event.group import IEventGroup

class RegistrationField(object):

    attrs = {
            'type' : 'field',
            'title' : '',
            'default' : '',
            'is_require' : False,
            'options' : [],
    }

    def __init__(self, **kwargs):

        self.data = {}

        for (k,v) in self.attrs.iteritems():

            value = kwargs.get(k, v)

            self.data[k] = value

        for k in ('default', 'options'):
            if not self.data[k]:
                del self.data[k]

        self.data['sort_order'] = 0

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

    fields = [
        RegistrationField(
            type='ticket_type',
            title='Ticket Type',
            is_require=True,
            default='Standard',
        ),
        RegistrationField(
            type='firstname',
            title='First Name',
            is_require=True,
        ),
        RegistrationField(
            type='lastname',
            title='Last Name',
            is_require=True,
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

    fields = [
        RegistrationField(
            title='Company Name',
        ),
        RegistrationField(
            title='Job Title',
        ),
    ]

class AccessibilityRegistrationFields(BaseRegistrationFields):

    label = "Accessibility"
    sort_order = 30

    fields = [
        RegistrationField(
            title='Do you require assistance?',
            options=['Audio', 'Visual', 'Mobile'],
            type='checkbox',
        )
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