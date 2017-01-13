from . import EventGroup, IEventGroup
from agsci.atlas.content.behaviors import IOptionalVideo

class IConferenceGroup(IEventGroup, IOptionalVideo):
    pass

class ConferenceGroup(EventGroup):
    pass
