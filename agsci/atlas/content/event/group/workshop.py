from . import EventGroup, IEventGroup
from agsci.atlas.content.behaviors import IOptionalVideo

class IWorkshopGroup(IEventGroup, IOptionalVideo):
    pass

class WorkshopGroup(EventGroup):
    pass
