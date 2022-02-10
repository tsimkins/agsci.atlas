from plone.dexterity.content import Container
from agsci.atlas.content import IAtlasProduct

# Moved this class, and importing it here to avoid error.
from agsci.atlas.content.behaviors import IRegistrationFields

class IEventGroup(IAtlasProduct):
    pass

class EventGroup(Container):
    pass