from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider

from agsci.atlas.interfaces import IWebinarMarker
from .. import Event, IWebinarLocationEvent, IRegistrationEvent

@provider(IFormFieldProvider)
class IWebinar(IRegistrationEvent, IWebinarLocationEvent):

    __doc__ = "Webinar"

    # Hide the 'event_when_custom' field.
    form.omitted('event_when_custom')
    form.order_after(agenda="IEventBasic.end")
    form.order_after(credits="agenda")

class Webinar(Event):

    # Only allow one webinar recording inside a webinar.
    def allowedContentTypes(self):

        # If we find a recording, return an empty list
        if IWebinarMarker(self).getPages():
            return []

        # Otherwise, return the default.
        return super(Webinar, self).allowedContentTypes()