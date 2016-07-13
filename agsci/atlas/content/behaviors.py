from agsci.atlas import AtlasMessageFactory as _
from .vocabulary.calculator import AtlasMetadataCalculator, defaultMetadataFactory
from plone.app.event.dx.behaviors import IEventBasic as _IEventBasic
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from z3c.form.interfaces import IEditForm, IAddForm
from zope import schema
from zope.interface import provider, invariant, Invalid
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
                'atlas_category_level_3', 'atlas_filters'),
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

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=('sku', 'additional_information', 
                    'internal_comments', 'original_plone_ids'),
        )

    sku = schema.TextLine(
            title=_(u"SKU"),
            description=_(u""),
            required=False,
        )

    additional_information = schema.Text(
        title=_(u"Additional Information"),
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
class IAtlasProductMetadata(model.Schema):

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_home_or_commercial', 'atlas_language'),
    )
    
    atlas_home_or_commercial = schema.List(
        title=_(u"Home or Commercial"),
        value_type=schema.Choice(vocabulary="agsci.atlas.HomeOrCommercial"),
        required=False,
    )

    atlas_language = schema.List(
        title=_(u"Language"),
        description=_(u""),
        value_type=schema.Choice(vocabulary="agsci.atlas.Language"),
        required=True,
        defaultFactory=defaultLanguage,
    )

@provider(IFormFieldProvider)
class IAtlasEPASMetadata(model.Schema):

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_state_extension_team', 'atlas_program_team', 'atlas_curriculum',),
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

    @invariant
    def validateCurriculumCount(data):

        # Define min/max limits by type
        limits_by_type = {
            'Article' : (0,1),
            'Workshop' : (0,3),
            'Webinar' : (0,3),
            'Conference' : (0,3),
            'Cvent Event' : (0,3),
        }
        
        # Try to get the context (object we're working with) and on error, return None
        try:
            context = data.__context__
        except AttributeError:
            return None

        # Try to get the context's Type(), and on error, return None
        try:
            item_type = context.Type()
        except AttributeError:
            return None
       
        # If there are no constraints, return None
        if not limits_by_type.has_key(item_type):
            return None
        
        # Grab the min/max values
        (min_limit, max_limit) = limits_by_type.get(item_type)

        # Grab the number of Curriculum(s) selected
        curriculum_count = len(data.atlas_curriculum)
        
        # Verify that the curriculum_count is between the min and max
        if curriculum_count > max_limit or curriculum_count < min_limit:
            raise Invalid("Between %d and %d Curriculum(s) may be selected. There are currently %d selected." % (min_limit, max_limit, curriculum_count))
        
        # Everything's good!
        return None
    
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
            fields=('owners', 'authors'),
        )

    owners = schema.List(
            title=_(u"Owner"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            required=True
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


@provider(IFormFieldProvider)
class IAtlasCountyFields(model.Schema):

    county = schema.List(
        title=_(u"County"),
        description=_(u""),
        value_type=schema.Choice(vocabulary="agsci.atlas.County"),
        required=False
    )

@provider(IFormFieldProvider)
class IAtlasCounty(IAtlasCountyFields):

    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('county',),
        )

@provider(IFormFieldProvider)
class IAtlasLocation(IAtlasCountyFields):

    venue = schema.TextLine(
        title=_(u"Venue/Building Name"),
        required=False,
    )

    street_address = schema.Text(
        title=_(u"Street Address"),
        required=False,
    )

    city = schema.TextLine(
        title=_(u"City"),
        required=False,
    )
    
    state = schema.Choice(
        title=_(u"State"),
        vocabulary="agsci.person.states",
        required=False,
    )

    zip_code = schema.TextLine(
        title=_(u"ZIP Code"),
        required=False,
    )

    map_link = schema.TextLine(
        title=_(u"Map To Location"),
        description=_(u"e.g. Google Maps link"),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasContact(IAtlasLocation):

    phone_number = schema.TextLine(
        title=_(u"Phone Number"),
        required=False,
    )

    fax_number = schema.TextLine(
        title=_(u"Fax Number"),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasForSaleProduct(model.Schema):

    price = schema.Decimal(
        title=_(u"Price"),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasRegistration(IAtlasForSaleProduct):

    # Available to Public
    available_to_public = schema.Bool(
        title=_(u"Available to Public?"),
        description=_(u"This event is open to registration by anyone"),
        required=False,
        default=True,
    )

    # Registration
    
    registration_status = schema.Choice(
        title=_(u"Registration Status"),
        values=(u"Open", u"Closed"),
        required=False,
    )

    capacity = schema.Int(
        title=_(u"Capacity"),
        required=False,
    )

    registration_deadline = schema.Datetime(
        title=_(u"Registration Deadline"),
        required=False,
    )

    registrant_type = schema.Choice(
        title=_(u"Registrant Type"),
        values=(u"Registrant Type 1", u"Registrant Type 2"),
        required=False,
    )
    
    registration_help_name = schema.TextLine(
        title=_(u"Registration Help Name"),
        required=False,
    )

    registration_help_phone = schema.TextLine(
        title=_(u"Registration Help Phone"),
        required=False,
    )

    registration_help_email = schema.TextLine(
        title=_(u"Registration Help Email"),
        required=False,
    )

    walkin = schema.Choice(
        title=_(u"Walk-ins Accepted?"),
        values=(u"Yes", u"No"),
        required=False,
    )

    cancellation_deadline = schema.Datetime(
        title=_(u"Cancellation Deadline"),
        required=False,
    )