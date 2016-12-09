from agsci.atlas import AtlasMessageFactory as _
from plone.autoform import directives as form
from plone.supermodel import model
from .. import Event, ILocationEvent, IRegistrationEvent

class IWorkshop(IRegistrationEvent, ILocationEvent):

    form.omitted('length_content_access')

class Workshop(Event):
    pass