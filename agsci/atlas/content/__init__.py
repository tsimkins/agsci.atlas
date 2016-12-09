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

    pass

# Enumerate all schemas for content types and behaviors used by Atlas content

# Custom Atlas Schemas
from .behaviors import IAtlasMetadata, IAtlasProductMetadata, \
     IAtlasEPASMetadata, IAtlasOwnership, IAtlasAudience, IAtlasCounty, \
     IAtlasCountyFields, IAtlasContact, IAtlasLocation, IAtlasForSaleProduct, \
     IAtlasAudienceSkillLevel, IVideoBase, ICredits, IOptionalVideo, \
     IAtlasProductPageNote, IAtlasForSaleProductTimeLimited

from .article import IArticle

from .event.webinar import IWebinar

from .event.webinar.recording import IWebinarRecording, IWebinarPresentation, \
                                     IWebinarHandout

from .event.cvent import ICventEvent

from .publication import IPublication

from .curriculum import ICurriculum

from .video import IVideo

from .online_course import IOnlineCourse

# This list is referred to elsewhere.
atlas_schemas = (
                    IAtlasMetadata, IAtlasOwnership, IAtlasAudience,
                    IAtlasCounty, IAtlasCountyFields, IAtlasProductMetadata,
                    IAtlasEPASMetadata, IAtlasContact, IAtlasLocation, ICventEvent,
                    IAtlasForSaleProduct, IWebinar, IWebinarRecording,
                    IPublication, IAtlasAudienceSkillLevel, ICurriculum, IVideo,
                    IVideoBase, ICredits, IOptionalVideo, IWebinarPresentation,
                    IWebinarHandout, IOnlineCourse, IArticle, IAtlasProductPageNote,
                    IAtlasForSaleProductTimeLimited
                )