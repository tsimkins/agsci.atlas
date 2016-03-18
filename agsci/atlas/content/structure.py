from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IAtlasStructureMarker
from plone.dexterity.content import Container

class IAtlasStructure(model.Schema):

    pass

class ICategoryLevel1(IAtlasStructure):

    pass

class ICategoryLevel2(IAtlasStructure):

    pass

class ICategoryLevel3(IAtlasStructure):

    pass

@implementer(IAtlasStructureMarker)
class AtlasStructure(Container):
    
    pass
    
@adapter(ICategoryLevel1)
class CategoryLevel1(AtlasStructure):

    pass

@adapter(ICategoryLevel2)
class CategoryLevel2(AtlasStructure):

    pass

@adapter(ICategoryLevel3)
class CategoryLevel3(AtlasStructure):

    pass