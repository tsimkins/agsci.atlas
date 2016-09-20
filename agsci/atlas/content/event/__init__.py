from plone.autoform import directives as form
from plone.directives import form as p_d_f
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventMarker
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import Interface, Invalid, provider, implementer, invariant
from plone.app.contenttypes.interfaces import IEvent as _IEvent
from plone.app.textfield import RichText
from zope.schema.vocabulary import SimpleTerm
from group import IEventGroup
from .. import Container, IAtlasProduct
from ..behaviors import IAtlasLocation, IAtlasForSaleProduct, IAtlasRegistration, ICredits

# Event

contact_fields = []

location_fields = ['venue', 'street_address', 'city', 'state',
                   'zip_code', 'county', 'map_link']

registration_fields = ['registration_help_name', 'registration_help_email',
                       'registration_help_phone', 'registrant_type', 'walkin',
                       'registration_status', 'registration_deadline', 'capacity',
                       'cancellation_deadline', 'price', 'available_to_public']

categorization_fields = ['youth_event',]

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

class IRegistrationEvent(IEvent, IAtlasRegistration, IAtlasForSaleProduct):

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

@adapter(IEvent)
@implementer(IEventMarker)
class Event(Container):

    @property
    def timezone(self):
        return 'EST'

    def __setattr__(self, k, v):
        # NOOP if trying to set the time zone.
        if k == 'timezone':
            pass
        else:
            super(Event, self).__setattr__(k, v)

    # Gets the parent event group for the event
    def getParent(self):

        # Get the Plone parent of the event
        parent = self.aq_parent

        # If our parent is an event group, return the parent
        if IEventGroup.providedBy(parent):
            return parent

        return None

    # Returns the id of the parent event group, if it exists
    def getParentId(self):

        # Get the parent of the event
        parent = self.getParent()

        # If we have a parent
        if parent:
            # Return the Plone UID of the parent
            return parent.UID()

        return None

    # Returns the Bool value of 'available_to_public'
    # For some reason, this is not in the __dict__ of self.context, so we're
    # making a method to return it, and calling it directly in the API. Bool
    # weirdness?
    def isAvailableToPublic(self):
        return getattr(self, 'available_to_public', True)
        
    # Returns the Bool value of 'youth_event'
    # Same reason as above.
    def isYouthEvent(self):
        return getattr(self, 'youth_event', False)
