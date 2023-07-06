from Acquisition import aq_base
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.content import ContentHistoryView
from plone.dexterity.interfaces import IDexterityContent
from plone.indexer import indexer
from plone.namedfile.file import NamedBlobFile
from zope.component import provideAdapter
from zope.globalrequest import getRequest

from .content import IAtlasProduct, IArticleDexterityContainedContent
from .content.adapters import HideFromSitemapAdapter
from .content.behaviors import IAtlasInternalMetadata, IAtlasOwnership, \
                               IAtlasFilterSets, IAtlasProductAttributeMetadata, \
                               defaultLanguage, IHomepageTopics, IAtlasDepartments
from .content.article import IArticle
from .content.adapters import PDFDownload
from .content.check import getValidationErrors
from .content.event import IEvent
from .content.event.cvent import ICventEvent
from .content.event.group import IEventGroup
from .content.structure import IAtlasStructure
from .content.vocabulary.calculator import AtlasMetadataCalculator

from .constants import INTERNAL_STORE_CATEGORY_LEVEL_1

from .utilities import isInternalStore, isExternalStore, \
                       get_last_modified_by_content_owner, \
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


# Indexers for **structure** departments
@indexer(IAtlasDepartments)
def AtlasDepartments(context):

    _ = getattr(aq_base(context), 'departments')

    if _ and isinstance(_, (list, tuple)):
        return _

    return []

provideAdapter(AtlasDepartments, name='Departments')


# Indexers for Extension structure metadata
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

# Is this a featured product on L1?
@indexer(IAtlasProduct)
def IsFeaturedProductL1(context):
    return not not getattr(aq_base(context), 'is_featured_l1', False)

provideAdapter(IsFeaturedProductL1, name='IsFeaturedProductL1')

# Is this a featured product on L2?
@indexer(IAtlasProduct)
def IsFeaturedProductL2(context):
    return not not getattr(aq_base(context), 'is_featured_l2', False)

provideAdapter(IsFeaturedProductL2, name='IsFeaturedProductL2')

# Is this a featured product on L3?
@indexer(IAtlasProduct)
def IsFeaturedProductL3(context):
    return not not getattr(aq_base(context), 'is_featured_l3', False)

provideAdapter(IsFeaturedProductL3, name='IsFeaturedProductL3')

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

# Hide From Site Map
@indexer(IAtlasProduct)
def HideFromSitemap(context):

    adapted = HideFromSitemapAdapter(context)
    return adapted.hide_from_sitemap

provideAdapter(HideFromSitemap, name='hide_from_sitemap')

@indexer(IAtlasInternalMetadata)
def IsExternalStore(context):
    return isExternalStore(context)

provideAdapter(IsExternalStore, name='IsExternalStore')

@indexer(IAtlasInternalMetadata)
def IsInternalStore(context):
    return isInternalStore(context)

provideAdapter(IsInternalStore, name='IsInternalStore')

@indexer(IEventGroup)
def HasUpcomingEvents(context):

    now = DateTime()

    for o in context.listFolderContents():
        if getattr(o, 'sku', None): # If there's a SKU, it's been imported into Magento
            if IEvent.providedBy(o): # If our child is an event.
                if hasattr(o, 'start'): # If the start date is after the current time, we have an upcoming event.
                    if DateTime(o.start) > now:
                        return True

    return False

provideAdapter(HasUpcomingEvents, name='HasUpcomingEvents')

@indexer(IAtlasProduct)
def AutomaticallyExpired(context):

    # Start of review process
    expires_min = DateTime('2023-01-01')
    request = getRequest()

    wftool = getToolByName(context, "portal_workflow")
    
    review_state = wftool.getInfoFor(context, 'review_state')
    
    if review_state in ('archived', 'expired'):

        v = ContentHistoryView(context, request)
    
        history = v.workflowHistory()
    
        history = [x for x in history if x.get('time', None) and x['time'] >= expires_min]
    
        if history:
    
            actions = [x['action'] for x in history]
    
            if 'expired' in actions:
    
                expired = [x for x in history if x['state_title'] == 'Expired']
    
                if expired:
                    comments = expired[0].get('comments', '')
                    return comments and 'Automatically expired' in comments

    return False

provideAdapter(AutomaticallyExpired, name='AutomaticallyExpired')

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
