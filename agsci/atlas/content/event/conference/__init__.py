from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider
from .. import Event, ILocationEvent, IRegistrationEvent

@provider(IFormFieldProvider)
class IConference(IRegistrationEvent, ILocationEvent):
    pass

class Conference(Event):
    pass