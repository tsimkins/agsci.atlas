from Products.CMFCore.utils import getToolByName
from collective.dexteritytextindexer import searchable
from collective.dexteritytextindexer.behavior import IDexterityTextIndexer
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from datetime import datetime
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.dexterity.behaviors.metadata import IPublication as _IPublication
from plone.app.event.dx.behaviors import IEventBasic as _IEventBasic
from plone.app.event.dx.behaviors import StartBeforeEnd
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.formwidget.contenttree import ObjPathSourceBinder
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from z3c.relationfield.schema import RelationChoice, RelationList
from zope import schema
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import Interface, provider, invariant, Invalid
from zope.schema.interfaces import IContextAwareDefaultFactory, IVocabularyFactory

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import IAtlasProduct
from agsci.atlas.permissions import *

from ..geo import LatLngFieldWidget
from ..publication import IPublication
from ..vocabulary.calculator import defaultMetadataFactory
from ..widgets import DatetimeFieldWidget

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

    # Determined based on 'create' URL.

    both_stores = [2,3]

    external_store = [2,]

    both_stores_types = [
        'atlas_publication',
    ]

    # Check the portal_type
    portal_type = getattr(context, 'portal_type', None)

    if portal_type and portal_type in both_stores_types:
        return both_stores

    # Check the request URL
    request = getRequest()

    request_url = request.getURL()

    if request_url and any(['++add++%s' % x in request_url for x in both_stores_types]):
        return both_stores

    #External Store Onlly
    return external_store

internal_fields = ['sku', 'store_view_id', 'internal_comments',
                   'original_plone_ids', 'original_plone_site', 'magento_url',
                   'magento_image_url', 'hide_product']

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
    searchable('sku')

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

    hide_product = schema.Bool(
        title=_(u"Hide product from listings."),
        description=_(u""),
        required=False,
        default=False,
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

            else:

                # Verify that we have a valid object with a UID
                if context and hasattr(context, 'UID'):

                    # Check for the uniqueness of the SKU.  This will raise an
                    # error if the SKU exists elsewhere.
                    return isUniqueSKU(sku, context.UID())

                else:
                    return isUniqueSKU(sku)

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

    atlas_food_type = schema.List(
        title=_(u"Food Type"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.FoodType"),
        required=False,
    )

    atlas_cow_age_lactation_stage = schema.List(
        title=_(u"Cow Age or Lactation Stage"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.CowAgeLactationStage"),
        required=False,
    )

    atlas_poultry_flock_size = schema.List(
        title=_(u"Flock Size"),
        value_type=schema.Choice(vocabulary="agsci.atlas.filter.PoultryFlockSize"),
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


# Schema for defining alternate language version of content
class IAlternateLanguageRowSchema(Interface):

    language = schema.Choice(
        title=_(u"Language"),
        vocabulary="agsci.atlas.Language",
        required=False,
    )

    sku = schema.TextLine(
        title=_(u"SKU"),
        required=False
    )

@provider(IFormFieldProvider)
class IAtlasProductAttributeMetadata(IAtlasFilterSets):

    __doc__ = "Product Attributes"

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=(
            'atlas_language', 'atlas_home_or_commercial',
            'atlas_agronomic_crop', 'atlas_business_topic',
            'atlas_cover_crop', 'atlas_disaster', 'atlas_energy_source',
            'atlas_farm_structure', 'atlas_forage_crop', 'atlas_fruit',
            'atlas_industry', 'atlas_insect_pests', 'atlas_plant_diseases',
            'atlas_plant_type', 'atlas_turfgrass', 'atlas_vegetable',
            'atlas_water_source', 'atlas_weeds', 'atlas_food_type',
            'atlas_cow_age_lactation_stage', 'atlas_poultry_flock_size',
        ),
    )

    # Internal
    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['atlas_alternate_language'],
    )

    form.write_permission(atlas_alternate_language=ATLAS_SUPERUSER)

    form.order_after(atlas_alternate_language='IHomepageFeature.homepage_feature')

    form.widget(atlas_alternate_language=DataGridFieldFactory)

    atlas_language = schema.List(
        title=_(u"Language"),
        description=_(u""),
        value_type=schema.Choice(vocabulary="agsci.atlas.Language"),
        required=True,
        defaultFactory=defaultLanguage,
    )

    atlas_alternate_language = schema.List(
        title=u"Alternate Language Versions",
        value_type=DictRow(title=u"Language", schema=IAlternateLanguageRowSchema),
        required=False
    )


@provider(IFormFieldProvider)
class IAtlasEPASMetadata(model.Schema):

    __doc__ = "EPAS Metadata"

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=(
            'epas_unit', 'epas_team', 'epas_topic', 'epas_primary_team',
        ),
    )

    # Updated EPAS Structure

    epas_unit = schema.List(
        title=_(u"Unit"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.EPASUnit"),
    )

    epas_team = schema.List(
        title=_(u"Team"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.EPASTeam"),
    )

    epas_topic = schema.List(
        title=_(u"Topic"),
        description=_(u""),
        required=False,
        value_type=schema.Choice(vocabulary="agsci.atlas.EPASTopic"),
    )

    epas_primary_team = schema.Choice(
        title=_(u"Primary Team"),
        description=_(u""),
        required=False,
        vocabulary="agsci.atlas.EPASTeam",
    )

    # Ensure that a Primary EPAS Team is selected.  Specifically not checking
    # if this is a person.  And, if one EPAS Team is selected, that's the primary.
    @invariant
    def validatePrimaryEPASTeam(data):

        try:
            context = data.__context__

        except AttributeError:
            return None

        from agsci.person.content.person import IPerson

        if not IPerson.providedBy(context):

            epas_primary_team = getattr(data, 'epas_primary_team', None)
            epas_team = getattr(data, 'epas_team', None)

            if not epas_primary_team:

                if epas_team and len(epas_team) > 1:
                    raise Invalid("Extension Reporting: Primary Team is required.")

@provider(IFormFieldProvider)
class IAtlasPersonEPASMetadata(IAtlasEPASMetadata):

    # People don't need topics
    form.omitted('epas_team', 'epas_topic', 'epas_primary_team')

    # Limit setting teams to superusers
    form.write_permission(
        epas_unit=ATLAS_SUPERUSER,
        epas_team=ATLAS_SUPERUSER,
        epas_topic=ATLAS_SUPERUSER,
        epas_primary_team=ATLAS_SUPERUSER,
    )

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
    #model.fieldset(
    #        'categorization',
    #        label=_(u'Categorization'),
    #        fields=('atlas_audience', 'atlas_knowledge'),
    #    )

    form.order_after(atlas_knowledge='IRichText.text')
    form.order_after(atlas_audience='IRichText.text')

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

    #model.fieldset(
    #    'categorization',
    #    label=_(u'Categorization'),
    #    fields=('atlas_skill_level',),
    #)

    form.order_after(atlas_skill_level='IRichText.text')
    form.order_after(atlas_knowledge='IRichText.text')
    form.order_after(atlas_audience='IRichText.text')

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
        description=_(u"Penn State id (xyz5000), one per line."),
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
        description=_(u"Penn State id (xyz5000), one per line."),
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

    # Omit values set from Google Maps
    form.omitted(
        'geocode_types',
        'geocode_place_id',
        'formatted_address',
    )

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

    geocode_types = schema.List(
        title=_(u"Geocoded Address Types"),
        required=False,
        value_type=schema.TextLine(required=False),
    )

    geocode_place_id = schema.TextLine(
        title=_(u"Google Maps Place Id"),
        description=_(u""),
        required=False,
    )

    formatted_address= schema.TextLine(
        title=_(u"Google Maps Formatted Address"),
        description=_(u""),
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

    # Omit registrant_type
    form.omitted('registrant_type')

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
        values=(u"Active", u"Closed", u"Completed", u"Cancelled"),
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

@provider(IFormFieldProvider)
class IEventFees(model.Schema):

    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['fees', ]
    )

    fees = RichText(
        title=_(u"Event Fee Details"),
        required=False
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

    form.write_permission(
        video_provider=ATLAS_SUPERUSER,
        video_aspect_ratio=ATLAS_SUPERUSER,
        video_channel_id=ATLAS_SUPERUSER,
    )

    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['video_provider', 'video_aspect_ratio', 'video_channel_id'],
    )

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

# Credit Type selectable on the event group
@provider(IFormFieldProvider)
class IEventGroupCredits(model.Schema):

    __doc__ = "Credits/CEUs (Event Group)"

    # Credit
    credit_type = schema.List(
        title=_(u"Credit Type"),
        value_type=schema.Choice(vocabulary="agsci.atlas.CreditType"),
        required=False,
    )

    # Credit Category
    credit_category = schema.List(
        title=_(u"Credit Category"),
        value_type=schema.Choice(vocabulary="agsci.atlas.CreditCategory"),
        required=False,
    )

@provider(IFormFieldProvider)
class IPublicationCredits(IEventGroupCredits):

    __doc__ = "Credits/CEUs (Publication)"

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

    __doc__ = "Purchase Publication Version"

    form.write_permission(
        article_purchase=ATLAS_SUPERUSER,
        article_purchase_internal=ATLAS_SUPERUSER,
        publication_reference_number=ATLAS_SUPERUSER,
        price=ATLAS_SUPERUSER,
        publication_expire=ATLAS_SUPERUSER,
    )

    # Make publication_reference_number searchable
    searchable('publication_reference_number')

    # Internal
    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=[
            'article_purchase',
            'article_purchase_internal',
            'publication_expire',
            'publication_reference_number',
            'price',
        ],
    )

    article_purchase = schema.Bool(
        title=_(u"Article available for purchase?"),
        description=_(u"Makes print publication available on internal and external stores."),
        default=False,
        required=False
    )

    article_purchase_internal = schema.Bool(
        title=_(u"Article available for purchase on internal store only?"),
        description=_(u"Sets the store ids to the internal store only for the print publication."),
        default=False,
        required=False
    )

    publication_reference_number = schema.TextLine(
        title=_(u"Publication Reference Number"),
        description=_(u"SKU of print publication associated with this article."),
        required=False,
    )

    publication_expire = schema.Bool(
        title=_(u"Expire associated publication."),
        description=_(u"This will set the status of the associated publication for Magento and Salesforce."),
        required=False,
        default=False,
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
    form.write_permission(
        homepage_topics=ATLAS_SUPERUSER,
        is_featured=ATLAS_SUPERUSER,
        is_featured_l1=ATLAS_SUPERUSER,
        is_featured_l2=ATLAS_SUPERUSER,
        is_featured_l3=ATLAS_SUPERUSER,
    )

    # Hide M1 featured field
    form.mode(is_featured='hidden')

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=[
                'homepage_topics',
                'is_featured_l1',
                'is_featured_l2',
                'is_featured_l3',
            ]
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

    is_featured_l1 = schema.Bool(
        title=_(u"Feature on Category 1 Page"),
        description=_(u"This product will be featured on the Category Level 1 page"),
        required=False,
        default=False,
    )

    is_featured_l2 = schema.Bool(
        title=_(u"Feature on Category 2 Page"),
        description=_(u"This product will be featured on the Category Level 2 page"),
        required=False,
        default=False,
    )

    is_featured_l3 = schema.Bool(
        title=_(u"Feature on Category 3 Page"),
        description=_(u"This product will be featured on the Category Level 3 page"),
        required=False,
        default=False,
    )

@provider(IFormFieldProvider)
class IBasicTitle(IBasic):
    form.omitted('description')
    form.mode(description='hidden')

# Manually select related products
@provider(IFormFieldProvider)
class IRelatedProducts(model.Schema):

    # Internal tab
    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['related_products',],
    )

    # Only allow superusers to write to this field
    form.write_permission(related_products=ATLAS_SUPERUSER)

    # Relation field, only showing Products that are not child products
    related_products = RelationList(
        title=_(u"Related Products"),
        default=[],
        value_type=RelationChoice(
            title=u"Related",
            source=ObjPathSourceBinder(
                object_provides=IAtlasProduct.__identifier__,
                IsChildProduct=[None,False],
            ),
        ),
        required=False,
    )

# Publication / Expiration dates with an effective date that allows dates more
# than ten years prior.
@provider(IFormFieldProvider)
class IPublication(_IPublication):

    effective = schema.Datetime(
        title=_(u'label_effective_date', u'Publishing Date'),
        description=_(
            u'help_effective_date',
            default=u'If this date is in the future, the content will '
                    u'not show up in listings and searches until this date.'),
        required=False,
        min=datetime(1990, 1, 1),
    )

    form.widget(effective=DatetimeFieldWidget)

# Publishing / Expired Dates with role check
@provider(IFormFieldProvider)
class IRestrictedExpiration(IPublication):

    form.write_permission(
        expires=ATLAS_SUPERUSER,
    )


# Publishing / Expired Dates with role check
@provider(IFormFieldProvider)
class IRestrictedPublication(IPublication):

    form.write_permission(
        effective=ATLAS_SUPERUSER,
        expires=ATLAS_SUPERUSER,
    )

# App Available Format Row Schema
class IAppAvailableFormatRowSchema(Interface):

    title = schema.Choice(
        title=_(u"App Store"),
        vocabulary="agsci.atlas.app_available_formats",
        required=False,
    )

    description = schema.TextLine(
        title=_(u"Description"),
        required=False,
        max_length=25,
    )

    url = schema.TextLine(
        title=_(u"Download URL"),
        required=False
    )

# App Available Format
@provider(IFormFieldProvider)
class IAppAvailableFormat(model.Schema):

    __doc__ = "App Available Formats"

    form.widget(available_formats=DataGridFieldFactory)
    form.write_permission(available_formats=ATLAS_SUPERUSER)

    # Available Formats
    available_formats = schema.List(
        title=u"Available Formats",
        value_type=DictRow(title=u"Format", schema=IAppAvailableFormatRowSchema),
        required=False
    )

    # Ensure that type name/optional description is unique within the app
    @invariant
    def validateUniqueTypes(data):
        try:
            available_formats = data.available_formats
        except AttributeError:
            pass
        else:

            def getKey(v):
                fields = ('title', 'description')
                return tuple([v.get(x, '') for x in fields])

            keys = [getKey(x) for x in available_formats]

            duplicate_keys = [x for x in set(keys) if keys.count(x) > 1]

            if duplicate_keys:
                raise Invalid(_("Available Format Value %r used multiple times." % duplicate_keys))

# Link Status Report
class ILinkStatusReportRowSchema(Interface):

    title = schema.TextLine(
        title=_(u"Link title"),
        required=False,
    )

    url = schema.TextLine(
        title=_(u"Link URL"),
        required=False
    )

    status = schema.Int(
        title=_(u"Status Code"),
        required=False,
    )

    redirect_url = schema.TextLine(
        title=_(u"Redirect URL"),
        required=False
    )

@provider(IFormFieldProvider)
class ILinkStatusReport(model.Schema):

    __doc__ = "Report of Link Status"

    form.widget(link_report=DataGridFieldFactory)
    form.omitted('link_report', 'link_report_date')

    link_report = schema.List(
        title=u"Link Status",
        value_type=DictRow(title=u"Format", schema=ILinkStatusReportRowSchema),
        required=False
    )

    link_report_date = schema.Datetime(
        title=_(u'Link report Date'),
        required=False,
    )

# Configure Gated Content
@provider(IFormFieldProvider)
class IGatedContent(model.Schema):

    __doc__ = "Gated Content"

    # Only allow superusers to write to this field
    form.write_permission(
        is_gated_content=ATLAS_SUPERUSER,
        gated_url=ATLAS_SUPERUSER
    )

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['is_gated_content', 'gated_url',]
        )

    is_gated_content = schema.Bool(
        title=_(u"Is Gated Content?"),
        description=_(u""),
        required=False,
        default=False,
    )

    gated_url = schema.TextLine(
        title=_(u"URL For Gated Content"),
        description=_(u""),
        required=False,
    )

# Schema for defining product positions by SKU
class IProductPositionsRowSchema(Interface):

    sku = schema.Choice(
        title=_(u"SKU"),
        vocabulary="agsci.atlas.CategorySKUs",
        required=False
    )

    position = schema.Int(
        title=_(u"Position"),
        required=False
    )

@provider(IFormFieldProvider)
class IProductPositions(model.Schema):

    form.widget(product_positions=DataGridFieldFactory)

    product_positions = schema.List(
        title=u"Sort Order For Products",
        value_type=DictRow(title=u"Language", schema=IProductPositionsRowSchema),
        required=False
    )

@provider(IFormFieldProvider)
class IOmitProducts(model.Schema):

    # Only allow superusers to write to thes fields
    form.write_permission(
        omit_magento=ATLAS_SUPERUSER,
    )

    # Internal
    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=[
            'omit_magento'
        ],
    )

    omit_magento = schema.Bool(
        title=_(u"Omit product from Magento"),
        description=_(u""),
        required=False,
        default=False,
    )

@provider(IFormFieldProvider)
class IAtlasDepartments(model.Schema):

    # Only allow superusers to write to thes fields
    form.write_permission(
        departments=ATLAS_SUPERUSER,
    )

    departments = schema.List(
        title=_(u"Departments"),
        description=_(u"Departments under which this should be shown on their Extension section."),
        value_type=schema.Choice(vocabulary="agsci.atlas.Departments"),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasCategoryDepartments(IAtlasDepartments):

    model.fieldset(
        'settings',
        label=_(u'Settings'),
        fields=['departments',],
    )

@provider(IFormFieldProvider)
class IAtlasProductDepartments(IAtlasDepartments):

    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['departments',],
    )

@provider(IFormFieldProvider)
class IEventGroupPolicies(model.Schema):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['policies', 'custom_policy']
    )

    policies = schema.List(
        title=_(u"Event Group Policies"),
        description=_(u"Determines which policy statements are shown on the event group in Magento"),
        value_type=schema.Choice(vocabulary="agsci.atlas.EventGroupPolicy"),
        required=False,
    )

    custom_policy = RichText(
        title=_(u"Custom Policy"),
        required=False
    )

@provider(IFormFieldProvider)
class IProductFAQ(model.Schema):

    # Only allow superusers to write to thes fields
    form.write_permission(
        faq=ATLAS_SUPERUSER,
    )

    # Internal Fieldset
    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['faq',],
    )

    faq = schema.Choice(
        title=_(u"Alternate FAQ"),
        description=_(u"For products that have an FAQ that is not the default for the product type."),
        vocabulary="agsci.atlas.faq",
        required=False,
    )

@provider(IContextAwareDefaultFactory)
def defaultRegistrationFieldsets(context):

    vocab = getUtility(IVocabularyFactory, "agsci.atlas.RegistrationFieldsets")

    values = vocab(context)

    if values:
        return vocab.getDefaults(context)

@provider(IFormFieldProvider)

@provider(IFormFieldProvider)
class IRegistrationFields(model.Schema):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',],
    )

    # Registration Fields
    registration_fieldsets = schema.List(
        title=_(u"Registration Fieldsets"),
        description=_(u"Determines fields used in Magento registration form. "
                      u"Defaults are 'Minimal', 'Marketing', and 'Accessibility'"
                      u", and these will be used even if deselected."),
        value_type=schema.Choice(vocabulary="agsci.atlas.RegistrationFieldsets"),
        required=False,
        defaultFactory=defaultRegistrationFieldsets
    )