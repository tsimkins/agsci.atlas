from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from zope import schema
from zope.interface import provider
from .. import Container, IAtlasProduct
from ..behaviors import IOptionalVideo, ICredits
from ..event import IRegistrationFields
from plone.supermodel import model

@provider(IFormFieldProvider)
class IOnlineCourse(IOptionalVideo, IAtlasProduct, ICredits, IRegistrationFields):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',],
    )

    # Put the "Sections" information at the bottom, and "Credits" below that.
    form.order_after(sections="IAtlasForSaleProductTimeLimited.length_content_access")
    form.order_after(credits="sections")

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['edx_id',],
        )

    # If this is empty, the value in the API output will be populated by the SKU
    edx_id = schema.TextLine(
        title=_(u"edX Id"),
        description=_(u"If different than SKU"),
        required=False,
    )

    # Number of sections/modules
    sections = schema.TextLine(
        title=_(u"Sections"),
        required=False,
    )

class OnlineCourse(Container):

    pass
