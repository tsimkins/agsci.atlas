from zope.interface import implementer

try:
    from zope.interface.interfaces import ObjectEvent, IObjectEvent
except ImportError:
    from zope.component.interfaces import ObjectEvent, IObjectEvent


# Lifecycle event that notifies that something has been imported.
class IAtlasImportEvent(IObjectEvent):
    pass

@implementer(IAtlasImportEvent)
class AtlasImportEvent(ObjectEvent):
    pass
