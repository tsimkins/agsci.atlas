from plone.autoform import directives as form
from plone.supermodel import model
from plone.dexterity.content import Container as _Container
from z3c.form.interfaces import IAddForm, IEditForm
from zope import schema

from agsci.atlas import AtlasMessageFactory as _

# Parent schema class for all products, and product contained content
class IAtlasProductAndContent(model.Schema):
    pass

# Parent schema class for all products
class IAtlasProduct(IAtlasProductAndContent):
    pass

# Parent class for all article content.  Used to indicate a piece of
# Dexterity content used in an article.  This interface allows us to
# trigger workflow on CRUD of article content types.

class IArticleDexterityContent(IAtlasProductAndContent):
    pass

class IArticleDexterityContainedContent(IArticleDexterityContent):
    pass

class Container(_Container):
    pass

# Enumerate all schemas for behaviors used by Atlas content

# Custom Atlas Schemas
from .behaviors import IAtlasInternalMetadata, IAtlasProductCategoryMetadata, \
     IAtlasProductAttributeMetadata, \
     IAtlasEPASMetadata, IAtlasOwnership, IAtlasOwnershipAndAuthors, \
     IAtlasAudience, IAtlasCounty, \
     IAtlasContact, IAtlasLocation, IAtlasForSaleProduct, IAtlasCountyContact, \
     IAtlasAudienceSkillLevel, \
     IAtlasProductPageNote, IAtlasForSaleProductTimeLimited, \
     IOnlineCourseEventDates, IArticlePurchase, IAppAvailableFormat, IOmitProducts

# This list is referred to elsewhere.
atlas_schemas = (
                    IAtlasInternalMetadata, IAtlasOwnership, IAtlasOwnershipAndAuthors,
                    IAtlasAudience, IAtlasCounty, IAtlasProductCategoryMetadata,
                    IAtlasProductAttributeMetadata,
                    IAtlasEPASMetadata, IAtlasContact, IAtlasLocation,
                    IAtlasForSaleProduct, IAtlasCountyContact,
                    IAtlasAudienceSkillLevel,
                    IAtlasProductPageNote,
                    IAtlasForSaleProductTimeLimited,
                    IOnlineCourseEventDates,
                    IArticlePurchase, IAppAvailableFormat, IOmitProducts
                )