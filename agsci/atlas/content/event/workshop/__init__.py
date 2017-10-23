from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from zope.interface import provider
from zope import schema

from agsci.atlas import AtlasMessageFactory as _

from .. import Event, ILocationEvent, IRegistrationEvent

@provider(IFormFieldProvider)
class IWorkshop(IRegistrationEvent, ILocationEvent):
    pass

class Workshop(Event):
    pass

@provider(IFormFieldProvider)
class IWorkshopExternal(IWorkshop):

    # Hide registration fields

    form.omitted(
        'capacity', 'registrant_type', 'walkin',
    )

    external_url = schema.TextLine(
        title=_(u"External Workshop URL"),
        description=_(u""),
        required=True,
    )