from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from .. import Event, IWebinarLocationEvent, IRegistrationEvent

class IWebinar(IRegistrationEvent, IWebinarLocationEvent):
    pass

class Webinar(Event):

    pass