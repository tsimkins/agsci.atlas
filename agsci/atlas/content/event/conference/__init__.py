from .. import Event, IEvent

class IConference(IEvent):
    pass

class Conference(Event):
    pass

class IComplexConference(IConference):
    pass

class ComplexConference(Conference):
    pass
