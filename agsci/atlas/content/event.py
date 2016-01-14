from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IEventsContainerMarker, IEventMarker
from plone.dexterity.content import Container
from plone.app.contenttypes.interfaces import IEvent as _IEvent

# Event container

class IEventsContainer(model.Schema):

    pass


@adapter(IEventsContainer)
@implementer(IEventsContainerMarker)
class EventsContainer(object):

    def __init__(self, context):
        self.context = context


# Event

class IEvent(_IEvent):

    pass


@adapter(IEvent)
@implementer(IEventMarker)
class Event(Container):

    pass
