from plone.autoform import directives as form
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventsContainerMarker, IEventMarker
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from plone.dexterity.content import Container
from plone.app.contenttypes.interfaces import IEvent as _IEvent
from plone.app.textfield import RichText
from zope.schema.vocabulary import SimpleTerm
from plone.app.event.dx.behaviors import IEventContact


# Event

contact_fields = ['contact_name', 'contact_email', 'contact_phone', 'registration_help_name', 
                       'registration_help_email',  'registration_help_phone',]

location_fields = ['venue', 'street_address', 'city', 'state', 
                   'zip_code', 'county', 'map_link']

registration_fields = ['registrant_type', 'walkin', 'registration_status', 
                       'registration_deadline', 'capacity', 
                       'cancellation_deadline', ]


class IEvent(model.Schema, _IEvent, IEventContact):

    model.fieldset(
        'location',
        label=_(u'Location'),
        fields=location_fields
    )

    model.fieldset(
        'contact',
        label=_(u'Contact Information'),
        fields=contact_fields
    )

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=registration_fields
    )

    form.omitted('event_url',)

    form.order_after(agenda="IRichText.text")
    
    # Agenda
    agenda = RichText(
        title=_(u"Agenda"),
        required=False,
    )

    # Location
    
    venue = schema.TextLine(
        title=_(u"Venue/Building Name"),
        required=False,
    )

    street_address = schema.Text(
        title=_(u"Street Address"),
        required=False,
    )

    city = schema.TextLine(
        title=_(u"City"),
        required=False,
    )

    state = schema.Choice(
        title=_(u"State"),
        vocabulary="agsci.person.states",
        required=False,
    )

    zip_code = schema.TextLine(
        title=_(u"ZIP Code"),
        required=False,
    )
   
    county = schema.Choice(
        title=_(u"County"),
        vocabulary="agsci.person.counties",
        required=False,
    )

    map_link = schema.TextLine(
        title=_(u"Map To Location"),
        description=_(u"e.g. Google Maps link"),
        required=False,
    )

    
    # Registration
    
    registration_status = schema.Choice(
        title=_(u"Registration Status"),
        values=(u"Open", u"Closed"),
        required=False,
    )

    capacity = schema.Int(
        title=_(u"Capacity"),
        required=False,
    )

    registration_deadline = schema.Datetime(
        title=_(u"Registration Deadline"),
        required=False,
    )

    registrant_type = schema.Choice(
        title=_(u"Registrant Type"),
        values=(u"Registrant Type 1", u"Registrant Type 2"),
        required=False,
    )
    
    registration_help_name = schema.TextLine(
        title=_(u"Registration Help Name"),
        required=False,
    )

    registration_help_phone = schema.TextLine(
        title=_(u"Registration Help Phone"),
        required=False,
    )

    registration_help_email = schema.TextLine(
        title=_(u"Registration Help Email"),
        required=False,
    )

    walkin = schema.Choice(
        title=_(u"Registration Status"),
        values=(u"Type 1", u"Type 2"),
        required=False,
    )

    cancellation_deadline = schema.Datetime(
        title=_(u"Cancellation Deadline"),
        required=False,
    )
    
@adapter(IEvent)
@implementer(IEventMarker)
class Event(Container):

    pass
