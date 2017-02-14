from agsci.atlas import AtlasMessageFactory as _
from plone.autoform import directives as form
from plone.supermodel import model
from .. import Event, ILocationEvent, IRegistrationEvent
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider

@provider(IFormFieldProvider)
class IWorkshop(IRegistrationEvent, ILocationEvent):
    pass

class Workshop(Event):
    pass