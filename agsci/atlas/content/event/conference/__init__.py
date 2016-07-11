from .. import Event, ILocationEvent

class IConference(ILocationEvent):
    pass

class Conference(Event):
    pass

class IComplexConference(IConference):
    pass

class ComplexConference(Conference):
    pass
