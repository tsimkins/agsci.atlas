from Acquisition import aq_base
from DateTime import DateTime
from plone.dexterity.interfaces import IDexterityContent
from plone.indexer import indexer
from plone.namedfile.file import NamedBlobFile
from zope.component import provideAdapter

from .content import IAtlasProduct, IArticleDexterityContainedContent
from .content.behaviors import IAtlasInternalMetadata, IAtlasOwnership, \
                               IAtlasFilterSets, IAtlasProductAttributeMetadata, \
                               defaultLanguage, IHomepageTopics
from .content.article import IArticle
from .content.adapters import PDFDownload
from .content.check import getValidationErrors
from .content.event.cvent import ICventEvent
from .content.structure import IAtlasStructure
from .content.vocabulary.calculator import AtlasMetadataCalculator

from .constants import INTERNAL_STORE_CATEGORY_LEVEL_1

from .utilities import isInternalStore, get_last_modified_by_content_owner, \
                       has_internal_store_categories

import hashlib

# Indexers for **content** using the Atlas metadata
@indexer(IAtlasInternalMetadata)
def AtlasOriginalPloneIds(context):

    return getattr(aq_base(context), 'original_plone_ids', [])

provideAdapter(AtlasOriginalPloneIds, name='OriginalPloneIds')

@indexer(IAtlasInternalMetadata)
def AtlasCategoryLevel1(context):

    c = getattr(aq_base(context), 'atlas_category_level_1', [])

    # If we have an internal item, and it doesn't have an internal store category,
    # add a fake Internal category so it shows up in the listing without it
    # actually being selected.
    if isInternalStore(context):

        if not has_internal_store_categories(context):
            if INTERNAL_STORE_CATEGORY_LEVEL_1 not in c:
                c.append(INTERNAL_STORE_CATEGORY_LEVEL_1)

    return c

provideAdapter(AtlasCategoryLevel1, name='CategoryLevel1')

@indexer(IAtlasInternalMetadata)
def AtlasCategoryLevel2(context):

    return getattr(aq_base(context), 'atlas_category_level_2', [])

provideAdapter(AtlasCategoryLevel2, name='CategoryLevel2')


@indexer(IAtlasInternalMetadata)
def AtlasCategoryLevel3(context):

    return getattr(aq_base(context), 'atlas_category_level_3', [])

provideAdapter(AtlasCategoryLevel3, name='CategoryLevel3')

@indexer(IAtlasInternalMetadata)
def EducationalDrivers(context):

    return getattr(aq_base(context), 'atlas_educational_drivers', [])

provideAdapter(EducationalDrivers, name='EducationalDrivers')

# Generic indexer for the category levels for structural elements.
def getAtlasCategoryIndex(context, level):

    mc = AtlasMetadataCalculator('CategoryLevel%d' % level)
    v = mc.getMetadataForObject(context)

    if v:
        return [v,]

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

# Old EPAS values
@indexer(IAtlasInternalMetadata)
def StateExtensionTeam(context):

    return getattr(aq_base(context), 'atlas_state_extension_team', [])

provideAdapter(StateExtensionTeam, name='StateExtensionTeam')

@indexer(IAtlasInternalMetadata)
def ProgramTeam(context):

    return getattr(aq_base(context), 'atlas_program_team', [])

provideAdapter(ProgramTeam, name='ProgramTeam')

@indexer(IAtlasInternalMetadata)
def Curriculum(context):

    return getattr(aq_base(context), 'atlas_curriculum', [])

provideAdapter(Curriculum, name='Curriculum')

# New EPAS values
@indexer(IAtlasInternalMetadata)
def EPASUnit(context):

    return getattr(aq_base(context), 'epas_unit', [])

provideAdapter(EPASUnit, name='EPASUnit')

@indexer(IAtlasInternalMetadata)
def EPASTeam(context):

    return getattr(aq_base(context), 'epas_team', [])

provideAdapter(EPASTeam, name='EPASTeam')

@indexer(IAtlasInternalMetadata)
def EPASTopic(context):

    return getattr(aq_base(context), 'epas_topic', [])

provideAdapter(EPASTopic, name='EPASTopic')

# Language
@indexer(IAtlasInternalMetadata)
def AtlasLanguage(context):

    _ = getattr(aq_base(context), 'atlas_language', [])

    if not _:
        return defaultLanguage(context)

provideAdapter(AtlasLanguage, name='atlas_language')


# Home or Commecial
@indexer(IAtlasInternalMetadata)
def AtlasHomeOrCommercial(context):

    return getattr(aq_base(context), 'atlas_home_or_commercial', [])

provideAdapter(AtlasHomeOrCommercial, name='HomeOrCommercial')


# Authors
@indexer(IAtlasOwnership)
def AtlasAuthors(context):

    v = getattr(aq_base(context), 'authors', [])

    if v:
        return v

    return []

provideAdapter(AtlasAuthors, name='Authors')


# Owners
@indexer(IAtlasOwnership)
def AtlasOwners(context):

    v = getattr(aq_base(context), 'owners', [])

    if v:
        return v

    return []

provideAdapter(AtlasOwners, name='Owners')


# Cvent ID
@indexer(ICventEvent)
def CventId(context):

    return getattr(aq_base(context), 'cvent_id', None)

provideAdapter(CventId, name='CventId')


# SKU
@indexer(IAtlasInternalMetadata)
def sku(context):

    return getattr(aq_base(context), 'sku', None)

provideAdapter(sku, name='SKU')


# MagentoURL
@indexer(IAtlasInternalMetadata)
def magento_url(context):

    return getattr(aq_base(context), 'magento_url', None)

provideAdapter(magento_url, name='MagentoURL')


# Salesforce Id
@indexer(IAtlasInternalMetadata)
def salesforce_id(context):

    return getattr(aq_base(context), 'salesforce_id', None)

provideAdapter(salesforce_id, name='SalesforceId')


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
    return tuple(sorted(set([x.error_code for x in errors])))


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

            f = getattr(aq_base(context), fname)

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
        return IAtlasProduct.providedBy(context) and IAtlasProduct.providedBy(context.aq_parent)
    except:
        return False

provideAdapter(IsChildProduct, name='IsChildProduct')

# Is this a featured product?
@indexer(IAtlasProduct)
def IsFeaturedProduct(context):
    return not not getattr(aq_base(context), 'is_featured', False)

provideAdapter(IsFeaturedProduct, name='IsFeaturedProduct')

@indexer(IAtlasInternalMetadata)
def IsHiddenProduct(context):
    return getattr(aq_base(context), 'hide_product', False)

provideAdapter(IsHiddenProduct, name='IsHiddenProduct')

# County for the item
@indexer(IAtlasProduct)
def ProductCounty(context):
    return getattr(aq_base(context), 'county', [])

provideAdapter(ProductCounty, name='County')

# Language
@indexer(IAtlasProductAttributeMetadata)
def ProductLanguage(context):
    return getattr(aq_base(context), 'atlas_language', [])

provideAdapter(ProductLanguage, name='atlas_language')

# Homepage Topics
@indexer(IHomepageTopics)
def HomepageTopics(context):
    return getattr(aq_base(context), 'homepage_topics', [])

provideAdapter(HomepageTopics, name='homepage_topics')

# Last Modified by a non-web person
@indexer(IAtlasProduct)
def ContentOwnerLastModified(context):

    (username, fullname, modified_date) = get_last_modified_by_content_owner(context)

    # Return the calculated modified date, if available
    if modified_date and isinstance(modified_date, DateTime):
        return modified_date

provideAdapter(ContentOwnerLastModified, name='content_owner_modified')

# Copyright year in PDF
@indexer(IArticle)
def ArticlePDFUpdatedYear(context):

    adapted = PDFDownload(context)
    return adapted.pdf_updated_year

provideAdapter(ArticlePDFUpdatedYear, name='pdf_updated_year')

# Return a list of filter set fields
def filter_sets():
    return IAtlasFilterSets.names()

# Function that returns a "get a value of this field" function
def filter_set_indexer(i):

    @indexer(IAtlasFilterSets)
    def f(context):
        v = getattr(aq_base(context), i, [])

        if v:
            return v
        return []

    return f

# Create indexers for each filter set
for filter_set in filter_sets():
    f = filter_set_indexer(filter_set)
    provideAdapter(f, name=filter_set)