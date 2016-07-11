from agsci.atlas.content.behaviors import IAtlasLocation
from .. import Event, ILocationEvent

class IWorkshop(ILocationEvent):
    pass

class Workshop(Event):
    pass

class IComplexWorkshop(IWorkshop):
    pass

class ComplexWorkshop(Workshop):
    pass
