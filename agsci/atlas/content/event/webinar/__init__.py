from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from .. import Event, IWebinarLocationEvent, IRegistrationEvent
from agsci.atlas.interfaces import IWebinarMarker
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider

@provider(IFormFieldProvider)
class IWebinar(IRegistrationEvent, IWebinarLocationEvent):

    __doc__ = "Webinar"

class Webinar(Event):

    # Only allow one webinar recording inside a webinar.
    def allowedContentTypes(self):

        # If we find a recording, return an empty list
        if IWebinarMarker(self).getPages():
            return []

        # Otherwise, return the default.
        return super(Webinar, self).allowedContentTypes()