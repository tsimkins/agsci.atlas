from .. import Event, IEvent

class IWebinar(IEvent):
    pass

class Webinar(Event):
    pass

class IComplexWebinar(IWebinar):
    pass

class ComplexWebinar(Webinar):
    pass