from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventsContainerMarker
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer


# Event container

class IEventsContainer(model.Schema):

    pass


@adapter(IEventsContainer)
@implementer(IEventsContainerMarker)
class EventsContainer(Container):

    pass
