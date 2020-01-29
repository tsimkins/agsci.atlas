from plone.dexterity.content import Container
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import IAtlasProduct
from ..behaviors import IOptionalVideo, IAtlasForSaleProductTimeLimited
from ..event.group import IRegistrationFields

class IOnlineCourseGroup(IOptionalVideo, IAtlasProduct, IRegistrationFields, \
                         IAtlasForSaleProductTimeLimited):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',],
    )

    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['allow_bulk_registration'],
    )

    # Order fields as: Sections, Length of Access
    form.order_after(sections="IEventGroupDuration.duration_hours_custom")
    form.order_after(length_content_access="sections")

    # Number of sections/modules
    sections = schema.Int(
        title=_(u"Sections"),
        required=False,
    )

    # Allow bulk registration
    allow_bulk_registration = schema.Bool(
        title=_(u"Allow bulk registration"),
        description=_(u""),
        default=False,
    )

class OnlineCourseGroup(Container):

    pass
