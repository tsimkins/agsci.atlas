from plone.autoform import directives as form
from plone.directives import form as p_d_f
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventMarker
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from plone.supermodel import model
from zope import schema
from zope.interface import Interface, Invalid, provider, implementer, invariant
from plone.app.contenttypes.interfaces import IEvent as _IEvent
from plone.app.textfield import RichText
from .. import Container, IAtlasProduct
from ..behaviors import IAtlasLocation, IAtlasRegistration, ICredits

# Event

contact_fields = []

location_fields = ['venue', 'street_address', 'city', 'state',
                   'zip_code', 'county', 'map_link', 'latitude', 'longitude']

registration_fields = ['registration_help_name', 'registration_help_email',
                       'registration_help_phone', 'registrant_type', 'walkin',
                       'registration_status', 'registration_deadline', 'capacity',
                       'cancellation_deadline', 'price', 'available_to_public',
                       'youth_event' ]

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
        except (TypeError, AttributeError):
            # Skip validation if there is no county selected
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

class IRegistrationEvent(IEvent, IAtlasRegistration):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=registration_fields
    )

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