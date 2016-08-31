from .content.behaviors import IAtlasMetadata, IAtlasOwnership
from .content.structure import IAtlasStructure
from .content.vocabulary.calculator import AtlasMetadataCalculator
from plone.indexer import indexer
from zope.component import provideAdapter

# Indexers for **content** using the Atlas metadata

@indexer(IAtlasMetadata)
def AtlasOriginalPloneIds(context):

    return getattr(context, 'original_plone_ids', [])

provideAdapter(AtlasOriginalPloneIds, name='OriginalPloneIds')

@indexer(IAtlasMetadata)
def AtlasCategoryLevel1(context):

    return getattr(context, 'atlas_category_level_1', [])

provideAdapter(AtlasCategoryLevel1, name='CategoryLevel1')

@indexer(IAtlasMetadata)
def AtlasCategoryLevel2(context):

    return getattr(context, 'atlas_category_level_2', [])

provideAdapter(AtlasCategoryLevel2, name='CategoryLevel2')


@indexer(IAtlasMetadata)
def AtlasCategoryLevel3(context):

    return getattr(context, 'atlas_category_level_3', [])

provideAdapter(AtlasCategoryLevel3, name='CategoryLevel3')

# Generic indexer for the category levels for structural elements.
def getAtlasCategoryIndex(context, level):

    mc = AtlasMetadataCalculator('CategoryLevel%d' % level)
    v = mc.getMetadataForObject(context)

    if v:
        return [v,]
    else:
        return []

# Indexers for **structure** using the Atlas metadata
@indexer(IAtlasStructure)
def AtlasStructureCategoryLevel1(context):

    return getAtlasCategoryIndex(context, 1)

provideAdapter(AtlasStructureCategoryLevel1, name='CategoryLevel1')

@indexer(IAtlasStructure)
def AtlasStructureCategoryLevel2(context):

    return getAtlasCategoryIndex(context, 2)

provideAdapter(AtlasStructureCategoryLevel2, name='CategoryLevel2')


@indexer(IAtlasStructure)
def AtlasStructureCategoryLevel3(context):

    return getAtlasCategoryIndex(context, 3)

provideAdapter(AtlasStructureCategoryLevel3, name='CategoryLevel3')

# Indexers for Extension structure metadata
@indexer(IAtlasMetadata)
def StateExtensionTeam(context):

    return getattr(context, 'atlas_state_extension_team', [])

provideAdapter(StateExtensionTeam, name='StateExtensionTeam')
    
@indexer(IAtlasMetadata)
def ProgramTeam(context):

    return getattr(context, 'atlas_program_team', [])

provideAdapter(ProgramTeam, name='ProgramTeam')

@indexer(IAtlasMetadata)
def Curriculum(context):

    return getattr(context, 'atlas_curriculum', [])

provideAdapter(Curriculum, name='Curriculum')


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

# Cvent ID

@indexer(IAtlasMetadata)
def CventId(context):

    return getattr(context, 'cvent_id', None)

provideAdapter(CventId, name='CventId')

# SKU

@indexer(IAtlasMetadata)
def sku(context):

    return getattr(context, 'sku', None)

provideAdapter(sku, name='SKU')
