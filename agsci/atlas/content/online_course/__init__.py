from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema
from zope.interface import provider

from .. import IAtlasProduct
from ..behaviors import ICredits, IAtlasForSaleProduct
from ..event import Event

@provider(IFormFieldProvider)
class IOnlineCourse(IAtlasProduct, ICredits, IAtlasForSaleProduct):

    __doc__ = "Online Course"

    # Order fields as: Price, Sections, Length of Access, Credits
    form.order_after(price="credits")
    form.order_after(credits="sections")
    form.order_after(credits="IAtlasForSaleProductTimeLimited.length_content_access")

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
    sections = schema.Int(
        title=_(u"Sections"),
        required=False,
    )

class OnlineCourse(Event):

    pass
