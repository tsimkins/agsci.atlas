from plone.autoform import directives as form
from plone.directives import form as p_d_f
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventMarker
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter, getUtility
from zope.interface import Interface, Invalid, provider, implementer, invariant
from plone.app.contenttypes.interfaces import IEvent as _IEvent
from plone.app.textfield import RichText
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import IContextAwareDefaultFactory, IVocabularyFactory
from .. import Container, IAtlasProduct
from ..behaviors import IAtlasLocation, IAtlasRegistration, ICredits

# Event

contact_fields = []

location_fields = ['venue', 'street_address', 'city', 'state',
                   'zip_code', 'county', 'map_link']

registration_fields = ['registration_help_name', 'registration_help_email',
                       'registration_help_phone', 'registrant_type', 'walkin',
                       'registration_status', 'registration_deadline', 'capacity',
                       'cancellation_deadline', 'price', 'available_to_public',
                       'registration_fieldsets', ]

categorization_fields = ['youth_event',]

@provider(IContextAwareDefaultFactory)
def defaultRegistrationFieldsets(context):

    vocab = getUtility(IVocabularyFactory, "agsci.atlas.RegistrationFieldsets")

    values = vocab(context)

    if values:
        return vocab.getDefaults(context)

class IAgendaRowSchema(Interface):

    time = schema.TextLine(
        title=u"Time",
        required=False
    )

    title = schema.TextLine(
        title=u"Title",
        required=False
    )

    description = schema.TextLine(
        title=u"Description",
        required=False
    )

class IEvent(IAtlasProduct, _IEvent, p_d_f.Schema, ICredits):

    form.order_after(agenda="IEventBasic.end")
    form.order_after(credits="agenda")
    form.widget(agenda=DataGridFieldFactory)

    # Agenda
    agenda = schema.List(
        title=u"Agenda",
        value_type=DictRow(title=u"Agenda Item", schema=IAgendaRowSchema),
        required=False
    )


class ILocationEvent(IEvent, IAtlasLocation):

    model.fieldset(
        'location',
        label=_(u'Location'),
        fields=location_fields
    )

    # Ensure that only one county is selected for this event.
    @invariant
    def validateSingleCounty(data):
        try:
            county = data.county

            if len(county) > 1:
                raise Invalid("Only one county may be selected for events.")
        except AttributeError:
            pass

class IWebinarLocationEvent(IEvent):

    model.fieldset(
        'location',
        label=_(u'Location'),
        fields=('webinar_url',),
    )

    webinar_url = schema.TextLine(
        title=_(u"Webinar Link"),
        required=True,
    )

class IRegistrationFields(model.Schema):

    registration_fieldsets = schema.List(
        title=_(u"Registration Fieldsets"),
        description=_(u"Determines fields used in Magento registration form. These "
                       "options are not shown if the Workshop/Webinar is part of "
                       " a Workshop/Webinar Group. "
                       "Defaults are 'Basic' and 'Accessibility', and these will "
                       "be used even if deselected."),
        value_type=schema.Choice(vocabulary="agsci.atlas.RegistrationFieldsets"),
        required=False,
        defaultFactory=defaultRegistrationFieldsets
    )

class IRegistrationEvent(IEvent, IAtlasRegistration, IRegistrationFields):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=registration_fields
    )

    model.fieldset(
        'categorization',
        label=_('Categorization'),
        fields=categorization_fields
    )

    form.order_after(youth_event="IAtlasAudienceSkillLevel.atlas_skill_level")

class Event(Container):

    @property
    def timezone(self):
        return 'America/New_York'

    def __setattr__(self, k, v):
        # NOOP if trying to set the time zone.
        if k == 'timezone':
            pass
        else:
            super(Event, self).__setattr__(k, v)