from Products.CMFCore.utils import getToolByName
from collective.dexteritytextindexer import searchable
from collective.dexteritytextindexer.behavior import IDexterityTextIndexer
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.event.dx.behaviors import IEventBasic as _IEventBasic
from plone.app.event.dx.behaviors import StartBeforeEnd
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.component.hooks import getSite
from zope.interface import Interface, provider, invariant, Invalid
from zope.schema.interfaces import IContextAwareDefaultFactory

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.permissions import *

from ..vocabulary.calculator import defaultMetadataFactory
from ..publication import IPublication
from ..geo import LatLngFieldWidget

import copy

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

@provider(IContextAwareDefaultFactory)
def defaultOwner(context):

    # Look up the currently logged in user
    portal_membership = getToolByName(context, 'portal_membership')
    user = portal_membership.getAuthenticatedMember()

    # If we have a user, return a list containing the username in unicode
    if user:
        return [unicode(user.getUserName()),]

    # If not, return an empty list
    return []

@provider(IContextAwareDefaultFactory)
def defaultStoreViewId(context):
    # Hardcoded based on Magento stores.
    # External=2, Internal=3

    # Publications are both, all others are External-only
    if IPublication.providedBy(context):
        return [2, 3]
    else:
        return [2]

internal_fields = ['sku', 'salesforce_id', 'store_view_id', 'internal_comments',
                   'original_plone_ids', 'original_plone_site', 'magento_url',
                   'magento_image_url']

social_media_fields = ['twitter_url', 'facebook_url', 'linkedin_url', 'google_plus_url']

# Validates that the SKU provided is unique in the site
def isUniqueSKU(sku, current_uid=None):

    # Nothing provided, and that's OK.
    if not sku:
        return True

    # Normalize by stripping whitespace and uppercasing
    sku = sku.strip().upper()

    # Get the catalog
    portal_catalog = getToolByName(getSite(), 'portal_catalog')

    # dict of normalized SKU to actual SKU.
    # Note uppercase of index name
    existing_sku = dict([(x.strip().upper(), x) for x in portal_catalog.uniqueValuesFor('SKU') if x])

    # If the normalized SKU exists
    if existing_sku.has_key(sku):

        # Query for the object with the actual SKU
        results = portal_catalog.searchResults({'SKU' : existing_sku[sku]})

        # If we find something, raise an error with that SKU and the path to the
        # existing object.
        if results:

            r = results[0]

            if r.UID != current_uid:
                raise Invalid("SKU '%s' already exists for %s" % (sku, r.getURL()))

        # If we were not provided with the current uid (e.g. assuming we're
        # checking when creating a new product), just raise an error.
        # This is for cases where the SKU is in the uniqueValuesFor, but the
        # user doesn't have permissions for the object.
        if not current_uid:
            raise Invalid("SKU '%s' already exists." % sku )

    return True


@provider(IFormFieldProvider)
class IAtlasInternalMetadata(model.Schema, IDexterityTextIndexer):

    __doc__ = "Basic Metadata"

    def getRestrictedFieldConfig():

        # Transform list into kw dictionary and return
        return dict([(x, ATLAS_SUPERUSER) for x in internal_fields])

    # Make SKU searchable
    searchable('sku', 'salesforce_id')

    # Internal
    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=internal_fields,
    )

    # Set write permissions on internal fields
    form.write_permission(**getRestrictedFieldConfig())

    sku = schema.TextLine(
        title=_(u"SKU"),
        description=_(u""),
        required=False,
    )

    salesforce_id = schema.TextLine(
        title=_(u"Salesforce Id"),
        description=_(u""),
        required=False,
    )

    store_view_id = schema.List(
        title=_(u"Store View"),
        description=_(u""),
        value_type=schema.Choice(vocabulary="agsci.atlas.StoreViewId"),
        defaultFactory=defaultStoreViewId,
        required=True,
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

    original_plone_site = schema.Text(
        title=_(u"Original Plone Site Domain"),
        required=False,
    )

    # These are set programatically, not in the UI
    form.omitted('magento_url', 'magento_image_url')

    magento_url = schema.TextLine(
        title=_(u"Magento Product URL"),
        description=_(u""),
        required=False,
    )

    magento_image_url = schema.TextLine(
        title=_(u"Magento Product Image URL"),
        description=_(u""),
        required=False,
    )

    # Ensure that SKU is unique within the site
    @invariant
    def validateUniqueSKU(data):
        sku = getattr(data, 'sku', None)

        if sku:

            # Try to get the context (object we're working with) and on error,
            # return None
            try:
                context = data.__context__
            except AttributeError:
                return None

            #  Check for the uniqueness of the SKU.  This will raise an error
            return isUniqueSKU(sku, context.UID())


    # Ensure that the store view id is populated
    @invariant
    def validateStoreViewId(data):

        store_view_id = getattr(data, 'store_view_id', None)

        if not store_view_id:
            raise Invalid("Store View is required.")

@provider(IFormFieldProvider)
class IAtlasFilterSets(model.Schema):

    __doc__ = "Product Attributes"

    atlas_home_or_commercial = schema.List(
        title=_(u"Home/Commercial"),
        value_type=schema.Choice(vocabulary="agsci.atlas.HomeOrCommercial"),
        required=False,
    )

    atlas_agronomic_crop = schema.List(
        title=_(u"Agronomic Crop"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.AgronomicCrop"),
        required=False,
    )

    atlas_business_topic = schema.List(
        title=_(u"Business Topic"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.BusinessTopic"),
        required=False,
    )

    atlas_cover_crop = schema.List(
        title=_(u"Cover Crop"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.CoverCrop"),
        required=False,
    )

    atlas_disaster = schema.List(
        title=_(u"Disaster"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.Disaster"),
        required=False,
    )

    atlas_energy_source = schema.List(
        title=_(u"Energy Source"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.EnergySource"),
        required=False,
    )

    atlas_farm_structure = schema.List(
        title=_(u"Farm Equipment/Structure"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.FarmEquipmentStructure"),
        required=False,
    )

    atlas_forage_crop = schema.List(
        title=_(u"Forage Crop"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.ForageCrop"),
        required=False,
    )

    atlas_fruit = schema.List(
        title=_(u"Fruit"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.Fruit"),
        required=False,
    )

    atlas_industry = schema.List(
        title=_(u"Industry"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.Industry"),
        required=False,
    )

    atlas_insect_pests = schema.List(
        title=_(u"Insect Pests"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.InsectPests"),
        required=False,
    )

    atlas_plant_diseases = schema.List(
        title=_(u"Plant Diseases"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.PlantDiseases"),
        required=False,
    )

    atlas_plant_type = schema.List(
        title=_(u"Plant Type"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.PlantType"),
        required=False,
    )

    atlas_turfgrass = schema.List(
        title=_(u"Turfgrass/Lawn"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.TurfgrassLawn"),
        required=False,
    )

    atlas_vegetable = schema.List(
        title=_(u"Vegetable"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.Vegetable"),
        required=False,
    )

    atlas_water_source = schema.List(
        title=_(u"Water Source"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.WaterSource"),
        required=False,
    )

    atlas_weeds = schema.List(
        title=_(u"Weeds"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.Weeds"),
        required=False,
    )

# Parent class for additional (non-IA) categories that are used to categorize
# content in Magento.  Example: Hot topics, recent articles, etc.
class IAdditionalCategories(model.Schema):

    __doc__ = "Additional Categories"

@provider(IFormFieldProvider)
class IAtlasProductCategoryMetadata(IAdditionalCategories):

    __doc__ = "Product Categories"

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_category_level_1', 'atlas_category_level_2',
                'atlas_category_level_3', 'atlas_educational_drivers'),
    )

    # Only allow superusers to write to this field
    form.write_permission(atlas_educational_drivers=ATLAS_SUPERUSER)

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

    atlas_educational_drivers = schema.List(
        title=_(u"Educational Drivers"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.educational_drivers"),
    )

@provider(IFormFieldProvider)
class IAtlasPersonCategoryMetadata(IAtlasProductCategoryMetadata):

    form.omitted('atlas_category_level_3', 'atlas_educational_drivers')


@provider(IFormFieldProvider)
class IAtlasProductAttributeMetadata(IAtlasFilterSets):

    __doc__ = "Product Attributes"

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_language', 'atlas_home_or_commercial',
                'atlas_agronomic_crop', 'atlas_business_topic',
                'atlas_cover_crop', 'atlas_disaster', 'atlas_energy_source',
                'atlas_farm_structure', 'atlas_forage_crop', 'atlas_fruit',
                'atlas_industry', 'atlas_insect_pests', 'atlas_plant_diseases',
                'atlas_plant_type', 'atlas_turfgrass', 'atlas_vegetable',
                'atlas_water_source', 'atlas_weeds'),
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

    __doc__ = "EPAS Metadata"

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
            'Article' : (0, 1),
            'Workshop' : (0, 3),
            'Webinar' : (0, 3),
            'Conference' : (0, 3),
            'Cvent Event' : (0, 3),
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

# Person version of EPAS data, omit curriculum.
@provider(IFormFieldProvider)
class IAtlasPersonEPASMetadata(IAtlasEPASMetadata):

    form.omitted('atlas_curriculum')

@provider(IFormFieldProvider)
class IAtlasProductPageNote(model.Schema):

    __doc__ = "Product Page Note"

    form.order_after(product_page_note='IBasic.description')

    # Product Page Note
    product_page_note = schema.Text(
        title=_(u"Product Page Note"),
        description=_(u"Short text to be featured in a callout on the product page."),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasAudience(model.Schema):

    __doc__ = "Audience (Basic)"

    # Categorization Fieldset
    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('atlas_audience', 'atlas_knowledge'),
        )

    atlas_audience = RichText(
        title=_(u"Who is this for?"),
        required=False
    )

    atlas_knowledge = RichText(
        title=_(u"What will you learn?"),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasAudienceSkillLevel(IAtlasAudience):

    __doc__ = "Audience Skill Level"

    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_skill_level',),
    )

    atlas_skill_level = schema.List(
        title=_(u"Skill Level(s)"),
        value_type=schema.Choice(vocabulary="agsci.atlas.SkillLevel"),
        required=False,
    )

class IExternalAuthorRowSchema(Interface):

    name = schema.TextLine(
        title=_(u"Name"),
        description=_(u""),
        required=False,
    )

    job_title = schema.TextLine(
        title=_(u"Job Title"),
        description=_(u""),
        required=False,
    )

    organization = schema.TextLine(
        title=_(u"Organization"),
        description=_(u""),
        required=False,
    )

    email = schema.TextLine(
        title=_(u"Email"),
        description=_(u""),
        required=False,
    )

    website = schema.TextLine(
        title=_(u"Website"),
        description=_(u""),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasOwnership(model.Schema):

    __doc__ = "Ownership"

    model.fieldset(
        'ownership',
        label=_(u'Ownership'),
        fields=('owners',),
    )

    owners = schema.List(
        title=_(u"Owner"),
        description=_(u""),
        value_type=schema.TextLine(required=True),
        defaultFactory=defaultOwner,
        required=True
    )

@provider(IFormFieldProvider)
class IAtlasOwnershipAndAuthors(IAtlasOwnership):

    __doc__ = "Ownership/Authors"

    model.fieldset(
        'ownership',
        label=_(u'Ownership'),
        fields=('authors', 'external_authors'),
    )

    form.widget(external_authors=DataGridFieldFactory)

    authors = schema.List(
        title=_(u"Authors / Instructors / Speakers"),
        description=_(u""),
        value_type=schema.TextLine(required=True),
        required=False
    )

    external_authors = schema.List(
        title=_(u"External Authors / Instructors / Speakers"),
        description=_(u"Individuals who are not part of Penn State Extension"),
        value_type=DictRow(title=u"People", schema=IExternalAuthorRowSchema),
        required=False
    )

@provider(IFormFieldProvider)
class IEventBasic(_IEventBasic):

    __doc__ = "Basic Event Information"

    form.omitted('whole_day','open_end', 'timezone')

@provider(IFormFieldProvider)
class IOnlineCourseEventDates(model.Schema):

    __doc__ = "Online Course Start/End Information"

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=('start', 'end', 'registration_deadline', 'capacity'),
    )

    start = schema.Datetime(
        title=_(u'Online Course Starts'),
        description=_(u'Date and Time, when the online course begins.'),
        required=False,
    )

    end = schema.Datetime(
        title=_(u'Online Course Ends'),
        description=_(u'Date and Time, when the online course ends.'),
        required=False,
    )

    registration_deadline = schema.Datetime(
        title=_(u"Registration Deadline"),
        required=False,
    )

    capacity = schema.Int(
        title=_(u"Capacity"),
        required=False,
    )

    @invariant
    def validate_start_end(data):
        if (
            data.start
            and data.end
            and data.start > data.end
        ):
            raise StartBeforeEnd(
                _(u"End date must be after start date.")
            )

        elif (data.start or data.end) and not (data.start and data.end):
            raise Invalid(_("Both start and end dates are required if one is selected."))


class IAtlasCountyFields(model.Schema):

    county = schema.List(
        title=_(u"County"),
        description=_(u""),
        value_type=schema.Choice(vocabulary="agsci.atlas.County"),
        required=False
    )

@provider(IFormFieldProvider)
class IAtlasCounty(IAtlasCountyFields):

    __doc__ = "County Data"

    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('county',),
    )

@provider(IFormFieldProvider)
class IAtlasLocation(IAtlasCountyFields):

    __doc__ = "Location Data"

    form.widget(latitude=LatLngFieldWidget)
    form.widget(longitude=LatLngFieldWidget)

    venue = schema.TextLine(
        title=_(u"Venue/Building Name"),
        required=False,
    )

    street_address = schema.List(
        title=_(u"Street Address"),
        required=False,
        value_type=schema.TextLine(required=False),
    )

    city = schema.TextLine(
        title=_(u"City"),
        required=False,
    )

    state = schema.Choice(
        title=_(u"State"),
        vocabulary="agsci.atlas.states",
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

    latitude = schema.Decimal(
        title=_(u"Latitude"),
        description=_(u"Decimal degrees, will be negative in southern hemisphere."),
        required=False,
    )

    longitude = schema.Decimal(
        title=_(u"Longitude"),
        description=_(u"Decimal degrees, will be negative in western hemisphere."),
        required=False,
    )


@provider(IFormFieldProvider)
class IAtlasContact(IAtlasLocation):

    __doc__ = "Contact Information"

    phone_number = schema.TextLine(
        title=_(u"Phone Number"),
        required=False,
    )

    fax_number = schema.TextLine(
        title=_(u"Fax Number"),
        required=False,
    )

class IAtlasSocialMediaBase(model.Schema):

    __doc__ = "Social Media"

    twitter_url = schema.TextLine(
        title=_(u"Twitter URL"),
        required=False,
    )

    facebook_url = schema.TextLine(
        title=_(u"Facebook URL"),
        required=False,
    )

    linkedin_url = schema.TextLine(
        title=_(u"LinkedIn URL"),
        required=False,
    )

    google_plus_url = schema.TextLine(
        title=_(u"Google+ URL"),
        required=False,
    )


class IAtlasSocialMedia(IAtlasSocialMediaBase):

    model.fieldset(
        'social-media',
        label=_(u'Social Media'),
        fields=social_media_fields,
    )

@provider(IFormFieldProvider)
class IAtlasCountyContact(IAtlasSocialMedia, IAtlasContact):

    form.order_after(county='IAtlasCountyContact.zip_code')

# This is just the price field.  It's broken out into the "...Base" class
# so as not to include price in the API output simply because we inherit
# from it.
class IAtlasForSaleProductBase(model.Schema):

    __doc__ = "For Sale Product Information"

    price = schema.Decimal(
        title=_(u"Price"),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasForSaleProduct(IAtlasForSaleProductBase):

    pass

@provider(IFormFieldProvider)
class IAtlasForSaleProductTimeLimited(model.Schema):

    __doc__ = "Length of Content Access"

    length_content_access = schema.Int(
        title=_(u"Length of Access"),
        description=_(u"If empty, unlimited."),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasRegistration(IAtlasForSaleProduct):

    __doc__ = "Event Registration Information"

    # Available to Public
    available_to_public = schema.Bool(
        title=_(u"Available to Public?"),
        description=_(u"This event is open to registration by anyone"),
        required=False,
        default=True,
    )

    # Youth Event
    youth_event = schema.Bool(
        title=_(u"Youth Event?"),
        description=_(u"This event is intended for youth."),
        required=False,
        default=False,
    )

    # Registration

    registration_status = schema.Choice(
        title=_(u"Registration Status"),
        values=(u"Active", u"Open", u"Closed", u"Completed", u"Cancelled"),
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

    walkin = schema.Bool(
        title=_(u"Walk-ins Accepted?"),
        required=False,
    )

    cancellation_deadline = schema.Datetime(
        title=_(u"Cancellation Deadline"),
        required=False,
    )

class IPDFDownload(model.Schema):

    __doc__ = "PDF Download"

    def getRestrictedFieldConfig():

        # Transform list into kw dictionary and return
        fields = [
            'pdf_autogenerate',
            'pdf_series',
            'pdf_column_count',
            'pdf_file',
        ]

        return dict([(x, ATLAS_SUPERUSER) for x in fields])

    # Set write permissions on internal fields
    form.write_permission(**getRestrictedFieldConfig())

    pdf_autogenerate = schema.Bool(
        title=_(u"Automatically generate PDF?"),
        required=False
    )

    pdf_series = schema.TextLine(
        title=_(u"Article Series (PDF)"),
        description=_(u"This will be shown on the auto-generated PDF."),
        required=False
    )

    pdf_column_count = schema.Choice(
        title=_(u"Article Column Count (PDF)"),
        description=_(u"Number of columns in the generated PDF."),
        values=('1', '2', '3', '4'),
        default='2',
        required=False,
    )

    pdf_file = NamedBlobFile(
        title=_(u"Article PDF File"),
        description=_(u"PDF Download for Article"),
        required=False,
    )

class IVideoBase(model.Schema):

    __doc__ = "Video (Basic)"

    video_url = schema.TextLine(
        title=_(u"Video URL"),
        required=True,
    )

    video_provider = schema.Choice(
        title=_(u"Video Provider"),
        vocabulary="agsci.atlas.VideoProviders",
        required=True,
        default=u"YouTube",
    )

    video_aspect_ratio = schema.Choice(
        title=_(u"Video Aspect Ratio"),
        vocabulary="agsci.atlas.VideoAspectRatio",
        required=True,
        default=u"16:9",
    )

    video_channel_id = schema.TextLine(
        title=_(u"Video Channel"),
        required=False,
    )

class IOptionalVideo(IVideoBase):

    __doc__ = "Video (Optional)"

    form.omitted('video_channel_id')

    # Duplicates the following fields from the IVideoBase parent schema, makes
    # a copy, and makes the copy not required.
    video_url = copy.copy(IVideoBase.get('video_url'))
    video_url.required = False

    video_provider = copy.copy(IVideoBase.get('video_provider'))
    video_provider.required = False

    video_aspect_ratio = copy.copy(IVideoBase.get('video_aspect_ratio'))
    video_aspect_ratio.required = False

class ICreditRowSchema(Interface):

    credit_type = schema.Choice(
        title=_(u"Credit Type"),
        vocabulary="agsci.atlas.CreditType",
        required=False,
    )

    credit_category = schema.Choice(
        title=_(u"Credit Category"),
        vocabulary="agsci.atlas.CreditCategory",
        required=False,

    )

    credit_value = schema.TextLine(
        title=_(u"Credit Value"),
        required=False
    )

class ICredits(model.Schema):

    __doc__ = "Credits/CEUs"

    form.widget(credits=DataGridFieldFactory)

    # Credit
    credits = schema.List(
        title=u"Credit/CEU Information",
        value_type=DictRow(title=u"Credit", schema=ICreditRowSchema),
        required=False
    )

# Duration (in hours) with a restricted custom field where the text needs to
# be more specific (e.g. "five two-hour classes over a period of ten weeks")
@provider(IFormFieldProvider)
class IEventGroupDuration(model.Schema):

    __doc__ = "Duration (Group Product)"

    form.write_permission(duration_hours_custom=ATLAS_SUPERUSER)

    form.order_after(duration_hours_custom='IAtlasProductPageNote.product_page_note')
    form.order_after(duration_hours='IAtlasProductPageNote.product_page_note')

    duration_hours = schema.Decimal(
        title=_(u"Duration (Hours)"),
        required=False
    )

    duration_hours_custom = schema.TextLine(
        title=_(u"Duration (Custom)"),
        description=_(u"Overrides the decimal number of hours with a text field."),
        required=False,
    )

# "Shadow" product parent behavior
# This is the parent behavior for "Shadow" products, which are maintained as one
# product in Plone, but require multiple product records in Salesforce or Magento.

class IShadowProduct(model.Schema):

    __doc__ = "Shadow product"


# "Sub Product" product parent behavior
# This is the parent behavior for sub-products, which are maintained as one
# product in Plone, but require multiple product records in Salesforce or Magento.
# These are exposed under the "contents" attribute in the API on the object. They
# are also considered "Shadow" products, and are exposed via the @@api call to
# the site root querying the latest updated items.

class ISubProduct(IShadowProduct):

    __doc__ = "Sub Product"


@provider(IFormFieldProvider)
class IArticlePurchase(IShadowProduct, IAtlasForSaleProductBase):

    __doc__ = "Fields that allow an article purchase"

    # Internal
    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['article_purchase', 'publication_reference_number', 'price'],
    )

    article_purchase = schema.Bool(
        title=_(u"Article available for purchase?"),
        default=False,
        required=False
    )

    publication_reference_number = schema.TextLine(
        title=_(u"Publication Reference Number"),
        description=_(u"SKU of print publication associated with this article."),
        required=False,
    )

class IPublicationFormat(Interface):

    sku = schema.TextLine(
            title=_(u"SKU"),
            description=_(u""),
            required=False,
        )

    format = schema.Choice(
        title=_(u"Format"),
        vocabulary="agsci.atlas.PublicationFormat",
        required=False,

    )

    price = schema.Decimal(
        title=_(u"Price"),
        required=False,
    )

@provider(IFormFieldProvider)
class IMultiFormatPublication(ISubProduct):

    __doc__ = "Multi-format Publication information"

    form.order_after(publication_formats='IAtlasForSaleProduct.price')

    form.widget(publication_formats=DataGridFieldFactory)

    # Credit
    publication_formats = schema.List(
        title=u"Publication Formats",
        value_type=DictRow(title=u"Format", schema=IPublicationFormat),
        required=False
    )


# Checkbox (for specific product types) to enable featuring on the homepage.
# This is used by an adapter to add a non-IA category
@provider(IFormFieldProvider)
class IHomepageFeature(IAdditionalCategories):

    __doc__ = "Homepage Feature"

    # Only allow superusers to write to this field
    form.write_permission(homepage_feature=ATLAS_SUPERUSER)

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['homepage_feature',]
        )

    homepage_feature = schema.Bool(
        title=_(u"Feature on Homepage"),
        description=_(u"This product will be featured on the homepage"),
        required=False,
        default=False,
    )


# Multi select list of Homepage Topics ("Hot Topics") that this product can be
# associated with
# This is used by an adapter to add a non-IA category
@provider(IFormFieldProvider)
class IHomepageTopics(IAdditionalCategories):

    __doc__ = "Homepage Topics"

    # Only allow superusers to write to this field
    form.write_permission(homepage_topics=ATLAS_SUPERUSER,
                          is_featured=ATLAS_SUPERUSER)

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['homepage_topics','is_featured']
        )

    homepage_topics = schema.List(
        title=_(u"Homepage Topic(s)"),
        description=_(u"This product will appear on the listing under this 'Hot Topic' on the homepage."),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.homepage_topics"),
    )

    is_featured = schema.Bool(
        title=_(u"Feature on Category 2 Page"),
        description=_(u"This product will be featured on the Category Level 2 page"),
        required=False,
        default=False,
    )

@provider(IFormFieldProvider)
class IBasicTitle(IBasic):
    form.omitted('description')
    form.mode(description='hidden')