from plone.supermodel import model
from plone.dexterity.content import Container
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from z3c.form.interfaces import IAddForm, IEditForm
from zope import schema
from zope.interface import provider
from agsci.atlas import AtlasMessageFactory as _
from  .behaviors import IAtlasLocation

@provider(IFormFieldProvider)
class ICounty(model.Schema):

    __doc__ = "County Information"

    title = schema.TextLine(
        title=_(u'label_title', default=u'Title'),
        required=True
    )

    office_hours = schema.List(
        title=_(u"Office Hours"),
        value_type=schema.TextLine(required=True),
        required=False,
    )

    email = schema.TextLine(
            title=_(u"Email"),
            description=_(u""),
            required=False,
    )

    client_relations_manager = schema.List(
        title=_(u"Client Relationship Manager"),
        value_type=schema.Choice(vocabulary="agsci.person.crm"),
        required=True,
    )

    business_operations_manager = schema.List(
        title=_(u"Business Operations Manager"),
        value_type=schema.Choice(vocabulary="agsci.person.bom"),
        required=True,
    )

    county_master_watershed_url = schema.TextLine(
        title=_(u"Master Watershed Stewards URL"),
        description=_(u"From https://extension.psu.edu/programs/watershed-stewards/counties"),
        required=False,
    )

    form.order_before(title='*')
    form.order_after(office_hours='IAtlasCountyContact.county')
    form.order_before(email='IAtlasCountyContact.phone_number')
    form.order_after(county_master_watershed_url='IAtlasCountyContact.fax_number')
    form.omitted('title')
    form.no_omit(IEditForm, 'title')
    form.no_omit(IAddForm, 'title')


class County(Container):

    exclude_schemas = [IAtlasLocation,]
