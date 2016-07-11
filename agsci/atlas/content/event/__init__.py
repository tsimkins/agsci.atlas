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
from group import IEventGroup
from ..behaviors import IAtlasLocation, IAtlasForSaleProduct

# Event

contact_fields = []

location_fields = ['venue', 'street_address', 'city', 'state', 
                   'zip_code', 'county', 'map_link']

registration_fields = ['registration_help_name', 'registration_help_email',  
                       'registration_help_phone', 'registrant_type', 'walkin', 
                       'registration_status', 
                       'registration_deadline', 'capacity', 
                       'cancellation_deadline', 'price']


class IEvent(model.Schema, _IEvent, IAtlasLocation, IAtlasForSaleProduct):

    model.fieldset(
        'location',
        label=_(u'Location'),
        fields=location_fields
    )

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=registration_fields
    )

    form.order_after(agenda="IRichText.text")
    
    # Agenda
    agenda = RichText(
        title=_(u"Agenda"),
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
        title=_(u"Walk-ins Accepted?"),
        values=(u"Yes", u"No"),
        required=False,
    )

    cancellation_deadline = schema.Datetime(
        title=_(u"Cancellation Deadline"),
        required=False,
    )
    
@adapter(IEvent)
@implementer(IEventMarker)
class Event(Container):

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