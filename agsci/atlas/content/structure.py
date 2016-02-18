from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IAtlasStructureMarker
from plone.dexterity.content import Container

class IAtlasStructure(model.Schema):

    magento_id = schema.Int(
        title=_(u"Magento Id"),
        required=True,
    )

class ICategory(IAtlasStructure):

    pass

class IProgram(IAtlasStructure):

    pass

class ITopic(IAtlasStructure):

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