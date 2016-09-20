from Products.CMFCore.utils import getToolByName
from collective.dexteritytextindexer import searchable
from collective.dexteritytextindexer.behavior import IDexterityTextIndexer
from plone.app.event.dx.behaviors import IEventBasic as _IEventBasic
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.component.hooks import getSite
from zope.interface import provider, invariant, Invalid, implementer
from zope.schema.interfaces import IContextAwareDefaultFactory

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IPDFDownloadMarker
from agsci.atlas.permissions import *

from ..pdf import AutoPDF
from ..vocabulary.calculator import defaultMetadataFactory

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
        return [ unicode(user.getUserName()), ]

    # If not, return an empty list
    return []

internal_fields = ['sku', 'additional_information', 'internal_comments',
                   'original_plone_ids']

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
class IAtlasMetadata(model.Schema, IDexterityTextIndexer):

    __doc__ = "Basic Metadata"

    def getRestrictedFieldConfig():

        # Transform list into kw dictionary and return
        return dict([(x, ATLAS_SUPERUSER) for x in internal_fields])

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_category_level_1', 'atlas_category_level_2',
                'atlas_category_level_3',),
    )

    # Make SKU searchable
    searchable('sku')

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

@provider(IFormFieldProvider)
class IAtlasProductMetadata(IAtlasFilterSets):

    __doc__ = "Product Attributes"

    # Categorization
    model.fieldset(
        'categorization',
        label=_(u'Categorization'),
        fields=('atlas_language', 'atlas_home_or_commercial',
                'atlas_agronomic_crop', 'atlas_business_topic',
                'atlas_cover_crop', 'atlas_disaster', 'atlas_energy_source',
                'atlas_farm_structure', 'atlas_forage_crop', 'atlas_fruit',
                'atlas_industry', 'atlas_plant_type', 'atlas_turfgrass',
                'atlas_vegetable', 'atlas_water_source'),
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

    __doc__ = "Filter Sets"

    # Categorization

    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('atlas_audience', 'atlas_knowledge'),
        )

    atlas_audience = schema.Text(
        title=_(u"Who is this for?"),
        required=False,
    )

    atlas_knowledge = schema.Text(
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

    atlas_skill_level = schema.Choice(
        title=_(u"Skill Level"),
        vocabulary="agsci.atlas.SkillLevel",
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasOwnership(model.Schema):

    __doc__ = "Ownership"

    model.fieldset(
            'ownership',
            label=_(u'Ownership'),
            fields=('owners', 'authors'),
        )

    owners = schema.List(
            title=_(u"Owner"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            defaultFactory=defaultOwner,
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

    __doc__ = "Basic Event Information"

    form.omitted('whole_day','open_end', 'timezone')


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

    __doc__ = "County Data"

    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('county',),
        )

@provider(IFormFieldProvider)
class IAtlasLocation(IAtlasCountyFields):

    __doc__ = "Location Data"

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

    __doc__ = "Contact Information"

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

    __doc__ = "For Sale Product Information"

    price = schema.Decimal(
        title=_(u"Price"),
        required=False,
    )

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

    link = schema.TextLine(
        title=_(u"Video Link"),
        required=True,
    )

    provider = schema.Choice(
        title=_(u"Video Provider"),
        vocabulary="agsci.atlas.VideoProviders",
        required=True,
        default=u"YouTube",
    )

    aspect_ratio = schema.Choice(
        title=_(u"Video Aspect Ratio"),
        vocabulary="agsci.atlas.VideoAspectRatio",
        required=True,
        default=u"16:9",
    )

    channel = schema.TextLine(
        title=_(u"Video Channel"),
        required=False,
    )

@adapter(IPDFDownload)
@implementer(IPDFDownloadMarker)
class PDFDownload(object):

    def __init__(self, context):
        self.context = context

    # Check for a PDF download or a
    def hasPDF(self):
        return getattr(self.context, 'pdf_file', None) or getattr(self.context, 'pdf_autogenerate', False)

    # Return the PDF data and filename, or (None, None)
    def getPDF(self):

        if self.hasPDF():
            # Since the filename calcuation logic is in the AutoPDF class, initialize
            # an instance, and grab the filename
            auto_pdf = AutoPDF(self.context)
            filename = auto_pdf.getFilename()

            # Check to see if we have an attached file
            pdf_file = getattr(self.context, 'pdf_file', None)

            # If we have an attached file, return that and the calculated filename
            if pdf_file:
                return (pdf_file.data, filename)

            # Otherwise, check for the autogenerate option
            elif getattr(self.context, 'pdf_autogenerate', False):
                return (auto_pdf.createPDF(), filename)

        # PDF doesn't exist or not enabled, return nothing
        return (None, None)