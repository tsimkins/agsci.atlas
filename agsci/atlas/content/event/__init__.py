from plone.autoform import directives as form
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventsContainerMarker, IEventMarker
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from plone.app.contenttypes.interfaces import IEvent as _IEvent
from plone.app.textfield import RichText
from zope.schema.vocabulary import SimpleTerm
from group import IEventGroup
from .. import Container
from ..behaviors import IAtlasLocation, IAtlasForSaleProduct, IAtlasRegistration

# Event

contact_fields = []

location_fields = ['venue', 'street_address', 'city', 'state', 
                   'zip_code', 'county', 'map_link']

registration_fields = ['registration_help_name', 'registration_help_email',  
                       'registration_help_phone', 'registrant_type', 'walkin', 
                       'registration_status', 'registration_deadline', 'capacity', 
                       'cancellation_deadline', 'price', 'available_to_public']
                
class IEvent(model.Schema, _IEvent):

    form.order_after(agenda="IRichText.text")
    
    # Agenda
    agenda = RichText(
        title=_(u"Agenda"),
        required=False,
    )


class ILocationEvent(IEvent, IAtlasLocation):

    model.fieldset(
        'location',
        label=_(u'Location'),
        fields=location_fields
    )

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
    
    # Returns the Bool value of 'available_to_public'
    # For some reason, this is not in the __dict__ of self.context, so we're
    # making a method to return it, and calling it directly in the API. Bool
    # weirdness?
    def isAvailableToPublic(self):
        return getattr(self, 'available_to_public', True)