from agsci.atlas.content.behaviors import IOptionalVideo
from . import EventGroup, IEventGroup

class IWorkshopGroup(IEventGroup, IOptionalVideo):
    pass

class WorkshopGroup(EventGroup):
    pass
