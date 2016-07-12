from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from .. import Event, ILocationEvent, IRegistrationEvent

class IWorkshop(IRegistrationEvent, ILocationEvent):
    pass

class Workshop(Event):
    pass