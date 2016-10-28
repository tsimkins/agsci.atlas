from . import EventGroup, IEventGroup
from agsci.atlas.content.behaviors import IOptionalVideo

class IWebinarGroup(IEventGroup, IOptionalVideo):
    pass

class WebinarGroup(EventGroup):
    pass
