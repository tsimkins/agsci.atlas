from zope.component.interfaces import ObjectEvent, IObjectEvent
from zope.interface import implementer

# Lifecycle event that notifies that something has been imported.
class IAtlasImportEvent(IObjectEvent):
    pass

@implementer(IAtlasImportEvent)
class AtlasImportEvent(ObjectEvent):
    pass