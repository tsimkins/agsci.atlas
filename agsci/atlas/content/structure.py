from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IAtlasStructureMarker
from plone.dexterity.content import Container

class ICategory(model.Schema):

    pass

class IProgram(model.Schema):

    pass

class ITopic(model.Schema):

    pass

@implementer(IAtlasStructureMarker)
class AtlasStructure(Container):
    
    pass
    
@adapter(ICategory)
class Category(AtlasStructure):

    pass

@adapter(IProgram)
class Program(AtlasStructure):

    pass

@adapter(ITopic)
class Topic(AtlasStructure):

    pass