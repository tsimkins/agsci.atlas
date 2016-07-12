from .. import Event, ILocationEvent
from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema

class IComplexEvent(ILocationEvent):
    pass
    

class ComplexEvent(Event):
    pass
