from .. import Event, IEventLocation

class IConference(IEventLocation):
    pass

class Conference(Event):
    pass

class IComplexConference(IConference):
    pass

class ComplexConference(Conference):
    pass
