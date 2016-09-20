from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from zope import schema
from zope.component import adapter
from zope.interface import provider
from . import Container, IAtlasProduct
from .behaviors import IVideoBase, ICredits
from plone.supermodel import model

import copy

@provider(IFormFieldProvider)
class IOnlineCourse(IVideoBase, IAtlasProduct, ICredits):

    # Hide the video 'channel' field
    form.omitted('channel')

    # Put the credits information at the bottom
    form.order_after(credits="IAtlasForSaleProduct.length_content_access")

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['edx_id',],
        )

    # Should this just be the SKU?
    edx_id = schema.TextLine(
        title=_(u"edX Id"),
        required=False,
    )

    # Duplicates the following fields from the IVideoBase parent schema, makes
    # a copy, and makes the copy not required.
    link = copy.copy(IVideoBase.get('link'))
    link.required = False

    provider = copy.copy(IVideoBase.get('provider'))
    provider.required = False

    aspect_ratio = copy.copy(IVideoBase.get('aspect_ratio'))
    aspect_ratio.required = False


@adapter(IOnlineCourse)
class OnlineCourse(Container):

    pass
