from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import provider

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IWebinarMarker
from agsci.atlas.permissions import *
from .. import Event, IWebinarLocationEvent, IRegistrationEvent

@provider(IFormFieldProvider)
class IWebinar(IRegistrationEvent, IWebinarLocationEvent):

    __doc__ = "Webinar"

    # Hide fields not needed for the webinar.
    form.omitted('event_when_custom', 'price', 'walkin')

    # Order fields
    form.order_after(agenda="IEventBasic.end")
    form.order_after(credits="agenda")

    # Only superusers can write to a few fields
    form.write_permission(
        registration_deadline=ATLAS_SUPERUSER,
        cancellation_deadline=ATLAS_SUPERUSER,
        capacity=ATLAS_SUPERUSER,
        original_cvent_id=ATLAS_SUPERUSER,
    )

    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=('original_cvent_id',),
    )

    original_cvent_id = schema.TextLine(
        title=_(u"Original Cvent Event Id"),
        description=_(u""),
        required=False,
    )

class Webinar(Event):

    # Only allow one webinar recording inside a webinar.
    def allowedContentTypes(self):

        # If we find a recording, return an empty list
        if IWebinarMarker(self).getPages():
            return []

        # Otherwise, return the default.
        return super(Webinar, self).allowedContentTypes()