from Acquisition import aq_base
from plone.dexterity.interfaces import IDexterityContent
from .content import IAtlasProduct, IArticleDexterityContainedContent
from .content.behaviors import IAtlasInternalMetadata, IAtlasOwnership, IAtlasFilterSets
from .content.event.cvent import ICventEvent
from .content.structure import IAtlasStructure
from .content.vocabulary.calculator import AtlasMetadataCalculator
from plone.indexer import indexer
from zope.component import provideAdapter
from .content.check import getValidationErrors

from plone.namedfile.file import NamedBlobFile

import hashlib

# Indexers for **content** using the Atlas metadata
@indexer(IAtlasInternalMetadata)
def AtlasOriginalPloneIds(context):

    return getattr(context, 'original_plone_ids', [])

provideAdapter(AtlasOriginalPloneIds, name='OriginalPloneIds')

@indexer(IAtlasInternalMetadata)
def AtlasCategoryLevel1(context):

    return getattr(context, 'atlas_category_level_1', [])

provideAdapter(AtlasCategoryLevel1, name='CategoryLevel1')

@indexer(IAtlasInternalMetadata)
def AtlasCategoryLevel2(context):

    return getattr(context, 'atlas_category_level_2', [])

provideAdapter(AtlasCategoryLevel2, name='CategoryLevel2')


@indexer(IAtlasInternalMetadata)
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
@indexer(IAtlasInternalMetadata)
def StateExtensionTeam(context):

    return getattr(context, 'atlas_state_extension_team', [])

provideAdapter(StateExtensionTeam, name='StateExtensionTeam')

@indexer(IAtlasInternalMetadata)
def ProgramTeam(context):

    return getattr(context, 'atlas_program_team', [])

provideAdapter(ProgramTeam, name='ProgramTeam')

@indexer(IAtlasInternalMetadata)
def Curriculum(context):

    return getattr(context, 'atlas_curriculum', [])

provideAdapter(Curriculum, name='Curriculum')


# Language
@indexer(IAtlasInternalMetadata)
def AtlasLanguage(context):

    return getattr(context, 'atlas_language', [])

provideAdapter(AtlasLanguage, name='Language')


# Home or Commecial
@indexer(IAtlasInternalMetadata)
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
@indexer(ICventEvent)
def CventId(context):

    return getattr(context, 'cvent_id', None)

provideAdapter(CventId, name='CventId')


# SKU
@indexer(IAtlasInternalMetadata)
def sku(context):

    return getattr(context, 'sku', None)

provideAdapter(sku, name='SKU')


# Content Issues
def ContentIssues(context):

    error_levels = ['High', 'Medium', 'Low']

    errors = [x.level for x in getValidationErrors(context)]
    error_summary = [errors.count(x) for x in error_levels]

    return tuple(error_summary)

@indexer(IAtlasProduct)
def ProductContentIssues(context):
    return ContentIssues(context)

@indexer(IArticleDexterityContainedContent)
def PageContentIssues(context):
    return ContentIssues(context)

provideAdapter(ProductContentIssues, name='ContentIssues')
provideAdapter(PageContentIssues, name='ContentIssues')

# Content Error Codes
def ContentErrorCodes(context):
    errors = getValidationErrors(context)
    return tuple(set([x.error_code for x in errors]))


@indexer(IAtlasProduct)
def ProductContentErrorCodes(context):
    return ContentErrorCodes(context)

provideAdapter(ProductContentErrorCodes, name='ContentErrorCodes')

@indexer(IDexterityContent)
def getFileChecksum(context):

    context = aq_base(context)

    fieldnames = ['file', 'pdf', 'pdf_file', 'pdf_sample', ]

    for fname in fieldnames:

        if hasattr(context, fname):

            f = getattr(context, fname)

            if isinstance(f, (NamedBlobFile,)):
                m = hashlib.md5()
                m.update(f.data)
                return m.hexdigest()

    return None

provideAdapter(getFileChecksum, name='cksum')

# Does this product have a parent that is a product
@indexer(IAtlasProduct)
def IsChildProduct(context):
    try:
        return IAtlasProduct.providedBy(context.aq_parent)
    except:
        return False

provideAdapter(IsChildProduct, name='IsChildProduct')

# Return a list of filter set fields
def filter_sets():
    return IAtlasFilterSets.names()

# Function that returns a "get a value of this field" function
def filter_set_indexer(i):

    @indexer(IAtlasFilterSets)
    def f(context):
        v = getattr(context, i, [])

        if v:
            return v
        return []

    return f

# Create indexers for each filter set
for filter_set in filter_sets():
    f = filter_set_indexer(filter_set)
    provideAdapter(f, name=filter_set)