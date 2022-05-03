from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from zope.interface import provider
from zope import schema

from agsci.atlas import AtlasMessageFactory as _

from .. import Event, ILocationEvent, IRegistrationEvent
from ..cvent import ICventProductDetailRowSchema

@provider(IFormFieldProvider)
class IExternalEvent(IRegistrationEvent, ILocationEvent):

    # Hide registration fields

    form.omitted(
        'capacity', 'registrant_type', 'walkin', 'product_detail',
    )

    form.widget(product_detail=DataGridFieldFactory)

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

    # Product Detail - used for import/export only. Not editable in Plone
    product_detail = schema.List(
        title=u"Cvent Product Detail",
        value_type=DictRow(title=u"Agenda Item", schema=ICventProductDetailRowSchema),
        required=False
    )

class ExternalEvent(Event):
    pass
