
from content.behaviors import IAtlasMetadata, IAtlasOwnership
from content.structure import IAtlasStructure
from plone.indexer import indexer
from zope.component import provideAdapter

# Indexers for content using the Atlas metadata
@indexer(IAtlasMetadata)
def AtlasCategory(context):

    return getattr(context, 'atlas_category', [])

provideAdapter(AtlasCategory, name='Category')

@indexer(IAtlasMetadata)
def AtlasProgram(context):

    return getattr(context, 'atlas_program', [])

provideAdapter(AtlasProgram, name='Program')


@indexer(IAtlasMetadata)
def AtlasTopic(context):

    return getattr(context, 'atlas_topic', [])

provideAdapter(AtlasTopic, name='Topic')

@indexer(IAtlasMetadata)
def AtlasFilters(context):

    return getattr(context, 'atlas_filters', [])

provideAdapter(AtlasFilters, name='Filters')

# Language

@indexer(IAtlasMetadata)
def AtlasLanguage(context):

    return getattr(context, 'atlas_language', [])

provideAdapter(AtlasLanguage, name='Language')

# Home or Commecial

@indexer(IAtlasMetadata)
def AtlasHomeOrCommercial(context):

    return getattr(context, 'atlas_home_or_commercial', [])

provideAdapter(AtlasHomeOrCommercial, name='HomeOrCommercial')

# Magento ID for the container (Category/Program/Topic) items.
@indexer(IAtlasStructure)
def AtlasMagentoId(context):
    return getattr(context, 'magento_id', None)

provideAdapter(AtlasMagentoId, name='MagentoId')

# Authors

@indexer(IAtlasOwnership)
def AtlasAuthors(context):

    v = getattr(context, 'authors', [])
    
    if v:
        return v
    
    return []

provideAdapter(AtlasAuthors, name='Authors')

# Owners
@indexer(IAtlasOwnership)
def AtlasOwners(context):

    v = getattr(context, 'owners', [])
    
    if v:
        return v
    
    return []

provideAdapter(AtlasOwners, name='Owners')