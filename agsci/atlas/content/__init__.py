from plone.autoform import directives as form
from plone.supermodel import model
from plone.dexterity.content import Container as _Container
from z3c.form.interfaces import IAddForm, IEditForm
from zope import schema

from agsci.atlas import AtlasMessageFactory as _

# Parent schema class for all products
class IAtlasProduct(model.Schema):
    pass

# Parent class for all article content.  Used to indicate a piece of  
# Dexterity content used in an article.  This interface allows us to
# trigger workflow on CRUD of article content types.

class IArticleDexterityContent(model.Schema):
    pass

class IArticleDexterityContainedContent(IArticleDexterityContent):

    # default fieldset
    title = schema.TextLine(
        title=_(u'label_title', default=u'Title'),
        required=True
    )

    form.order_before(title='*')
    
    form.omitted('title')
    form.no_omit(IEditForm, 'title')
    form.no_omit(IAddForm, 'title')
    
class Container(_Container):

    page_types = []
    
    def getPages(self):

        pages = self.listFolderContents({'Type' : self.page_types})
        
        return pages

# Enumerate all schemas for content types and behaviors used by Atlas content

# Custom Atlas Schemas
from .behaviors import IAtlasMetadata, IAtlasProductMetadata, \
     IAtlasEPASMetadata, IAtlasOwnership, IAtlasAudience, IAtlasCounty, \
     IAtlasCountyFields, IAtlasContact, IAtlasLocation, IAtlasForSaleProduct, \
     IAtlasAudienceSkillLevel

from .event import IEvent, _IEvent

from .event.webinar import IWebinar

from .event.webinar.recording import IWebinarRecording

from .event.cvent import ICventEvent

from .publication import IPublication

from .curriculum import ICurriculum

# This list is referred to elsewhere.
atlas_schemas = (
                    IAtlasMetadata, IAtlasOwnership, IAtlasAudience, IEvent,
                    _IEvent, IAtlasCounty, IAtlasCountyFields, IAtlasProductMetadata,
                    IAtlasEPASMetadata, IAtlasContact, IAtlasLocation, ICventEvent,
                    IAtlasForSaleProduct, IWebinar, IWebinarRecording,
                    IPublication, IAtlasAudienceSkillLevel, ICurriculum
                )