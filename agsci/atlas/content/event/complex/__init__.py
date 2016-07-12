from .. import Event, ILocationEvent
from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema

class IComplexEvent(ILocationEvent):

    atlas_event_type = schema.Choice(
        title=_(u"Event Type"),
        vocabulary="agsci.atlas.ComplexEventType",
        default=u"Workshop",
        required=True,
    )
    

class ComplexEvent(Event):
    pass
