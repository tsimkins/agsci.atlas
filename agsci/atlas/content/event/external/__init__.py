from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from zope.interface import provider
from zope import schema

from agsci.atlas import AtlasMessageFactory as _

from .. import Event, ILocationEvent, IRegistrationEvent

@provider(IFormFieldProvider)
class IExternalEvent(IRegistrationEvent, ILocationEvent):

    # Hide registration fields

    form.omitted(
        'capacity', 'registrant_type', 'walkin',
    )

    external_url = schema.TextLine(
        title=_(u"External Event URL"),
        description=_(u""),
        required=True,
    )

    atlas_event_type = schema.Choice(
        title=_(u"Event Type"),
        vocabulary="agsci.atlas.CventEventType",
        default=u"Workshop",
        required=True,
    )


class ExternalEvent(Event):
    pass
