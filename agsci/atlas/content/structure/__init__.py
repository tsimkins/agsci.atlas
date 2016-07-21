from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from agsci.atlas.interfaces import IAtlasStructureMarker
from plone.dexterity.content import Container

class IAtlasStructure(model.Schema):

    pass

class ICategoryLevel1(IAtlasStructure):

    pass

class ICategoryLevel2(IAtlasStructure):

    pass

class ICategoryLevel3(IAtlasStructure):

    atlas_filter_sets = schema.List(
        title=_(u"Filter Sets"),
        value_type=schema.Choice(vocabulary="agsci.atlas.FilterSet"),
        required=False,
    )

@implementer(IAtlasStructureMarker)
class AtlasStructure(Container):
    
    pass
    
@adapter(ICategoryLevel1)
class CategoryLevel1(AtlasStructure):

    pass

@adapter(ICategoryLevel2)
class CategoryLevel2(AtlasStructure):

    # Customize this method for Category Level 2, since we can have Products *or* 
    # a Category Level 3 inside, but not both.
    def allowedContentTypes(self):

        # Get existing allowed types
        allowed_content_types = super(CategoryLevel2, self).allowedContentTypes()    
        
        # Remove some content types if we have a Category Level 3 inside us        
        if self.listFolderContents({'Type' : 'CategoryLevel3'}):

            # Define permitted type ids
            restricted_to_types = [
                                    'atlas_category_level_3', 
                                    'atlas_events_container', 
                                    'atlas_news_container'
                                ]

            # This is the list we'll be returning
            final_types = []
            
            for i in allowed_content_types:
                if i.getId() in restricted_to_types:
                    final_types.append(i)

            return final_types

        return allowed_content_types

@adapter(ICategoryLevel3)
class CategoryLevel3(AtlasStructure):

    pass