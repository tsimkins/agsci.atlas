from .. import Event, ILocationEvent
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.permissions import *
from agsci.atlas.content.behaviors import IAtlasLocation, IAtlasRegistration
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from plone.supermodel import model
from zope import schema
from zope.interface import Interface
from plone.autoform import directives as form

class ICventProductDetailRowSchema(Interface):

    product_id = schema.TextLine(
        title=u"ProductID",
        required=False
    )

    product_name = schema.TextLine(
        title=u"ProductName",
        required=False
    )

    product_code = schema.TextLine(
        title=u"ProductCode",
        required=False
    )

    product_type = schema.TextLine(
        title=u"ProductType",
        required=False
    )

    product_description = schema.Text(
        title=u"ProductDescription",
        required=False
    )

    is_included = schema.Bool(
        title=_(u"IsIncluded"),
        required=False,
    )

    start_time = schema.Datetime(
        title=_(u"StartTime"),
        required=False,
    )

    end_time = schema.Datetime(
        title=_(u"EndTime"),
        required=False,
    )

    status = schema.TextLine(
        title=_(u"Status"),
        required=False,
    )

    capacity = schema.Int(
        title=_(u"C"),
        required=False,
    )

    session_category_name = schema.TextLine(
        title=u"SessionCategoryName",
        required=False
    )

    session_category_id = schema.TextLine(
        title=u"SessionCategoryID",
        required=False
    )

    educational_content = schema.Bool(
        title=_(u"EducationalContent"),
        required=False,
    )

    magento_agenda = schema.Bool(
        title=_(u"MagentoAgenda"),
        required=False,
    )


class ICventEvent(ILocationEvent, IAtlasRegistration):

    __doc__ = "Cvent Event"

    def getRestrictedFieldConfig():

        # Initialize display-only fields
        fields = ['cvent_id', 'cvent_url']

        # Transform list into kw dictionary and return
        return dict([(x, ATLAS_SUPERUSER) for x in fields])

    # Most of the Cvent fields should be set via the API push
    # and shouldn't be editable.
    def getOmittedFieldConfig():

        # Initialize fields
        fields = ['external_url', 'agenda', 'product_detail', 'county', 'price']

        # Hide location fields
        fields.extend(IAtlasLocation.names())

        # Hide registration fields
        fields.extend(IAtlasRegistration.names())

        return fields

    # Set ordering of fields
    form.order_after(credits="IEventBasic.end")
    form.widget(product_detail=DataGridFieldFactory)

    # Omit the fields that are only updateable by import
    form.omitted(*getOmittedFieldConfig())

    # Set write permissions for form.
    form.write_permission(**getRestrictedFieldConfig())

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

    external_url = schema.TextLine(
            title=_(u"Cvent Registration URL"),
            description=_(u""),
            required=False,
        )

    # Product Detail - used for import/export only. Not editable in Plone
    product_detail = schema.List(
        title=u"Cvent Product Detail",
        value_type=DictRow(title=u"Agenda Item", schema=ICventProductDetailRowSchema),
        required=False
    )


class CventEvent(Event):
    pass
