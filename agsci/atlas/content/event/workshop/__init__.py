from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from zope.interface import provider
from zope import schema

from agsci.atlas import AtlasMessageFactory as _

from .. import Event, ILocationEvent, IRegistrationEvent

@provider(IFormFieldProvider)
class IWorkshop(IRegistrationEvent, ILocationEvent):

    __doc__ = "Workshop"

class Workshop(Event):
    pass
