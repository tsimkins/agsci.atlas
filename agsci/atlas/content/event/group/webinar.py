from agsci.atlas.content.behaviors import IOptionalVideo
from . import EventGroup, IEventGroup

class IWebinarGroup(IEventGroup, IOptionalVideo):
    pass

class WebinarGroup(EventGroup):
    pass
