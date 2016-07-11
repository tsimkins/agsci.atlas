from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from .. import Event, IEvent

class IWebinar(IEvent):

    model.fieldset(
            'location',
            label=_(u'Location'),
            fields=('webinar_url',),
        )

    webinar_url = schema.TextLine(
        title=_(u"Webinar Link"),
        required=True,
    )

class Webinar(Event):

    page_types = ['Webinar Recording',]

class IComplexWebinar(IWebinar):
    pass

class ComplexWebinar(Webinar):
    pass