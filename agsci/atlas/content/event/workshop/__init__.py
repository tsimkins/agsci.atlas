from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider

from .. import Event, ILocationEvent, IRegistrationEvent

@provider(IFormFieldProvider)
class IWorkshop(IRegistrationEvent, ILocationEvent):
    pass

class Workshop(Event):
    pass