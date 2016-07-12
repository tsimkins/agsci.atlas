from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from .. import Event, ILocationEvent, IRegistrationEvent

class IConference(IRegistrationEvent, ILocationEvent):
    pass

class Conference(Event):
    pass