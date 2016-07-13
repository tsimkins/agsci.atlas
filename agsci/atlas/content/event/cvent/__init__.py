from .. import Event, ILocationEvent
from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema

class ICventEvent(ILocationEvent):

    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=('cvent_id', 'cvent_url'),
        )

    atlas_event_type = schema.Choice(
        title=_(u"Event Type"),
        vocabulary="agsci.atlas.CventEventType",
        default=u"Workshop",
        required=True,
    )

    cvent_id = schema.TextLine(
            title=_(u"Cvent Event Id"),
            description=_(u""),
            required=False,
        )

    cvent_url = schema.TextLine(
            title=_(u"Cvent Event URL"),
            description=_(u""),
            required=False,
        )

class CventEvent(Event):
    pass
