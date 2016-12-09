from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from .. import Event, IWebinarLocationEvent, IRegistrationEvent
from agsci.atlas.content.behaviors import IAtlasForSaleProductTimeLimited
from agsci.atlas.interfaces import IWebinarMarker

class IWebinar(IRegistrationEvent, IWebinarLocationEvent, IAtlasForSaleProductTimeLimited):

    __doc__ = "Webinar Information"

class Webinar(Event):

    # Only allow one webinar recording inside a webinar.
    def allowedContentTypes(self):

        # If we find a recording, return an empty list
        if IWebinarMarker(self).getPages():
            return []

        # Otherwise, return the default.
        return super(Webinar, self).allowedContentTypes()