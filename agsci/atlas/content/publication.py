from agsci.atlas import AtlasMessageFactory as _
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.interface import provider
from . import Container, IAtlasProduct
from agsci.atlas.permissions import *


@provider(IFormFieldProvider)
class IPublication(IAtlasProduct):

    __doc__ = "Publication"

    # Push bundle_publication_sku to internal fieldset, after sku
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['bundle_publication_sku'],
        )

    form.order_after(bundle_publication_sku='IAtlasInternalMetadata.sku')


    # Restrict writing to Atlas Superusers
    form.write_permission(bundle_publication_sku=ATLAS_SUPERUSER)

    bundle_publication_sku = schema.TextLine(
        title=_(u"SKU of Bundle Publication"),
        description=_(u"If this publication can be purchased as a bundle, indicate the bundle SKU here. Bundle price is in the 'price' field."),
        required=False,
    )

    pdf_sample = NamedBlobFile(
        title=_(u"Sample PDF"),
        description=_(u""),
        required=False,
    )

    pdf = NamedBlobFile(
        title=_(u"Downloadable PDF"),
        description=_(u""),
        required=False,
    )

    pages_count = schema.Int(
        title=_(u"Page Count"),
        description=_(u"Manually set page count."),
        required=False,
    )


class Publication(Container):

    pass