from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from zope import schema
from zope.interface import provider
from . import Container, IAtlasProduct
from .behaviors import IOptionalVideo, ICredits
from .event import IRegistrationFields
from plone.supermodel import model

@provider(IFormFieldProvider)
class IOnlineCourse(IOptionalVideo, IAtlasProduct, ICredits, IRegistrationFields):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',],
    )

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


class OnlineCourse(Container):

    pass
