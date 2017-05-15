from agsci.atlas.content.behaviors import IOptionalVideo
from . import EventGroup, IEventGroup

class IConferenceGroup(IEventGroup, IOptionalVideo):
    pass

class ConferenceGroup(EventGroup):
    pass
