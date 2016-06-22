from agsci.atlas import AtlasMessageFactory as _
from .vocabulary.calculator import AtlasMetadataCalculator, defaultMetadataFactory
from plone.app.event.dx.behaviors import IEventBasic as _IEventBasic
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from z3c.form.interfaces import IEditForm, IAddForm
from zope import schema
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory

@provider(IContextAwareDefaultFactory)
def defaultCategoryLevel1(context):
    return defaultMetadataFactory(context, 'CategoryLevel1')

@provider(IContextAwareDefaultFactory)
def defaultCategoryLevel2(context):
    return defaultMetadataFactory(context, 'CategoryLevel2')

@provider(IContextAwareDefaultFactory)
def defaultCategoryLevel3(context):
    return defaultMetadataFactory(context, 'CategoryLevel3')

@provider(IContextAwareDefaultFactory)
def defaultLanguage(context):
    return [u"English",]

@provider(IFormFieldProvider)
class IAtlasMetadata(model.Schema):

    # Categorization

    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_category_level_1', 'atlas_category_level_2', 
                'atlas_category_level_3', 'atlas_filters',
                'atlas_state_extension_team', 'atlas_program_team', 'atlas_curriculum',
                'atlas_language'),
    )

    atlas_category_level_1 = schema.List(
        title=_(u"Category Level 1"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.CategoryLevel1"),
        defaultFactory=defaultCategoryLevel1,
    )

    atlas_category_level_2 = schema.List(
        title=_(u"Category Level 2"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.CategoryLevel2"),
        defaultFactory=defaultCategoryLevel2,
    )

    atlas_category_level_3 = schema.List(
        title=_(u"Category Level 3"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.CategoryLevel3"),
        defaultFactory=defaultCategoryLevel3,
    )

    atlas_filters = schema.List(
        title=_(u"Filters"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.Filters"),
    )
        
    atlas_state_extension_team = schema.List(
        title=_(u"State Extension Team(s)"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.StateExtensionTeam"),
    )
    
    atlas_program_team = schema.List(
        title=_(u"Program Team(s)"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.ProgramTeam"),
    )

    atlas_curriculum = schema.List(
        title=_(u"Curriculum(s)"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.Curriculum"),
    )

    atlas_language = schema.List(
        title=_(u"Language"),
        description=_(u""),
        value_type=schema.Choice(vocabulary="agsci.atlas.Language"),
        required=True,
        defaultFactory=defaultLanguage,
    )

    additional_information = schema.Text(
        title=_(u"Additional Information"),
        required=False,
    )

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=('sku', 'internal_comments', 'original_plone_ids'),
        )

    sku = schema.TextLine(
            title=_(u"SKU"),
            description=_(u""),
            required=False,
        )

    internal_comments = schema.Text(
        title=_(u"Internal Comments"),
        required=False,
    )
    
    # Field to store original Plone UIDs from old Extension site

    original_plone_ids = schema.List(
        title=_(u"Original Plone Ids"),
        description=_(u""),
        value_type=schema.TextLine(required=True),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasAudience(model.Schema):

    # Categorization

    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('atlas_audience', 'atlas_knowledge', 'atlas_skill_level'),
        )

    atlas_audience = schema.Text(
        title=_(u"Who is this for?"),
        required=False,
    )

    atlas_knowledge = schema.Text(
        title=_(u"What will you learn?"),
        required=False,
    )

    atlas_skill_level = schema.Choice(
        title=_(u"Skill Level"),
        vocabulary="agsci.atlas.SkillLevel",
        required=False,
    )

class IAtlasPaid(model.Schema):

    length_content_access = schema.Int(
        title=_(u"Length of Access"),
        required=False,
    )


@provider(IFormFieldProvider)
class IAtlasOwnership(model.Schema):

    model.fieldset(
            'ownership',
            label=_(u'Ownership'),
            fields=('owners', 'contacts', 'authors'),
        )

    owners = schema.List(
            title=_(u"Owner"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            required=True
        )

    contacts = schema.List(
            title=_(u"Contacts"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            required=False
        ) 
        
    authors = schema.List(
            title=_(u"Authors / Instructors / Speakers"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            required=False
        ) 


@provider(IFormFieldProvider)
class IEventBasic(_IEventBasic):

    form.omitted('whole_day','open_end')
    model.fieldset('settings', fields=['timezone'],)

@provider(IFormFieldProvider)
class IAtlasComplexEvent(model.Schema):

    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=('cvent_id',),
        )

    cvent_id = schema.TextLine(
            title=_(u"Cvent Event Id"),
            description=_(u""),
            required=False,
        )