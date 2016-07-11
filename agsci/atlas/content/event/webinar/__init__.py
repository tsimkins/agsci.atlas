from agsci.atlas import AtlasMessageFactory as _
from zope import schema
from .. import Event, IEvent

class IWebinar(IEvent):
    
    link = schema.TextLine(
        title=_(u"Webinar Link"),
        required=True,
    )

class Webinar(Event):

    page_types = ['Webinar Recording',]

class IComplexWebinar(IWebinar):
    pass

class ComplexWebinar(Webinar):
    pass