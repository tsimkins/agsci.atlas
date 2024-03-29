from Acquisition import aq_base, aq_inner
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from datetime import datetime
from decimal import Decimal
from plone.app.versioningbehavior.behaviors import IVersionable
from plone.app.dexterity.behaviors.metadata import IPublication as _IPublication
from plone.app.layout.viewlets.common import GlobalSectionsViewlet as _GlobalSectionsViewlet
from plone.app.layout.viewlets.common import LogoViewlet as _LogoViewlet
from plone.app.layout.viewlets.common import PathBarViewlet as _PathBarViewlet
from plone.app.layout.viewlets.common import ViewletBase as _ViewletBase
from plone.app.layout.viewlets.content import HistoryByLineView
from plone.app.layout.viewlets.content import ContentHistoryViewlet
from plone.app.textfield.value import RichTextValue
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.interfaces import IDexterityEditForm
from plone.namedfile.file import NamedBlobFile
from plone.registry.interfaces import IRegistry
from zope import schema
from zope.component import getUtility, getMultiAdapter
from zope.interface.interface import Method
from zope.security import checkPermission
from zope.security.interfaces import NoInteraction

from agsci.atlas import object_factory

from agsci.atlas.constants import DELIMITER, ALLOW_FALSE_VALUES

from agsci.atlas.content.adapters import PDFDownload, CurriculumDataAdapter

from agsci.atlas.content.article import IArticle
from agsci.atlas.content.curriculum import ICurriculumDigital

from agsci.atlas.content.vocabulary import EducationalDriversVocabularyFactory
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.content import IAtlasProduct,  IArticleDexterityContent, \
                                IArticleDexterityContainedContent, atlas_schemas
from agsci.atlas.content.adapters import VideoDataAdapter
from agsci.atlas.content.check import getValidationErrors

from agsci.atlas.indexer import IsChildProduct
from agsci.atlas.interfaces import ILocationMarker

from agsci.atlas.permissions import ATLAS_SUPERUSER

from agsci.atlas.utilities import getBaseSchema, getAllSchemaFieldsAndDescriptions

from ..views import BaseView

import json
from urllib.parse import urlencode

try:
    from plone.protect.utils import addTokenToUrl
except ImportError:
    def addTokenToUrl(x):
        return x

class IPublication(_IPublication):
    __doc__ = "Publishing and Expiration Dates"

    effective = schema.Datetime(
        title=u"Publishing Date",
        description=u"",
        required=False,
    )

    expires = schema.Datetime(
        title=u"Expiration Date",
        description=u"",
        required=False,
    )

class ViewletBase(_ViewletBase):

    @property
    def is_admin(self):
        try:
            return checkPermission(ATLAS_SUPERUSER, self.context)
        except NoInteraction:
            return True

    @property
    def _portal_state(self):
        return getMultiAdapter((self.context, self.request),
                                name=u'plone_portal_state')

    @property
    def _context_state(self):
        return getMultiAdapter((self.context, self.request),
                                name=u'plone_context_state')

    @property
    def anonymous(self):
        return self._portal_state.anonymous()

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def registry(self):
        return getUtility(IRegistry)


class SchemaDump(object):

    def __init__(self, schema, context):

        self.schema = schema
        self.context = context
        self.fieldValues = self._fieldValues()

    def title(self):
        doc_string = getattr(self.schema, '__doc__', None)

        if doc_string:
            return doc_string

        return self.schema_name

    @property
    def schema_name(self):
        return self.schema.__name__

    def formatValue(self, x, key=''):
        if isinstance(x, (str, )):
            return x
        elif isinstance(x, (NamedBlobFile,)):
            url = '%s/@@download/%s' % (self.context.absolute_url(), key)
            return '<a href="%s">%s</a>' % (url, url)
        elif isinstance(x, (RichTextValue,)):
            return x.raw
        else:
            return repr(x)

    def hasFields(self):

        return len(self.fieldValues) > 0

    def _fieldValues(self):

        data = []

        def dataHasKey(data, key):
            keys = [x.get('id', '') for x in data]
            return key in keys

        for (key, field) in getAllSchemaFieldsAndDescriptions(self.schema):

            if dataHasKey(data, key):
                continue

            if isinstance(field, Method):
                continue

            if hasattr(self.context, key):
                value = getattr(self.context, key)

                if hasattr(value, '__call__'):
                    value = value()

                if isinstance(value, (datetime, DateTime)):

                    if hasattr(value.year, '__call__') and value.year() == 2499:
                        value = None
                    elif value.year == 2499:
                        value = None
                    else:
                        value = value.strftime('%Y-%m-%d %H:%M')

                if not isinstance(value, (list, tuple)):
                    value = [value,]

                value = [self.formatValue(x, key) for x in value if x or isinstance(x, ALLOW_FALSE_VALUES)]

                if value:

                    data.append(
                        {
                            'id' : key,
                            'name' : field.title,
                            'description' : field.description,
                            'value' : value,
                        }
                    )

        return data

class AtlasDataCheck(ViewletBase):

    def data(self):
        return getValidationErrors(self.context)

    def post_url(self):
        url = '%s/@@rescan' % self.context.absolute_url()

        return addTokenToUrl(url)


class AtlasDataDump(ViewletBase):

    def data(self):

        # Start with dates
        schema_data = [
            SchemaDump(IPublication, self.context),
        ]

        # Base schema
        schemas = [getBaseSchema(self.context),]

        # Copy the schemas list
        schemas.extend(atlas_schemas)

        # Remove any exclude_schemas from the object
        for exclude_schema in getattr(self.context, 'exclude_schemas', []):
            if exclude_schema in schemas:
                schemas.remove(exclude_schema)

        for schema in set(schemas):

            if schema.providedBy(self.context):
                if IFormFieldProvider.providedBy(schema):
                    schema_data.append(SchemaDump(schema, self.context))

        return schema_data

class JSONViewlet(ViewletBase):

    title = ""

    def comment(self):
        if self.title:
            return u"<!-- %s -->" % self.title

    # Determine if this is an edit or an add form.
    def show(self):
        if IAtlasProduct.providedBy(self.context) and IDexterityEditForm.providedBy(self.view):
            return True
        else:
            return isinstance(self.view, DefaultAddView)

class Category3AttributeSets(JSONViewlet):

    title = u"Dynamically generated JSON for Category 3 to Attribute Set Names"

    # Get a JSON output of a dict of CSS selector:filter sets for Category Level 3 objects
    def data(self):

        fmt = "#formfield-form-widgets-IAtlasProductAttributeMetadata-%s"

        values = {}

        results = self.portal_catalog.searchResults({'Type' : 'CategoryLevel3'})

        mc = AtlasMetadataCalculator('CategoryLevel3')

        for r in results:
            o = r.getObject()

            k = mc.getMetadataForObject(o)
            v = getattr(o, 'atlas_filter_sets', [])

            if v:
                values[k] = [fmt % x for x in v]

        return "var category_3_attribute_sets = %s" % json.dumps(values)

class Category1Hidden(JSONViewlet):

    title = u"Dynamically generated JSON for Category 1 items hidden from top nav"

    # Get a JSON output of a dict of CSS selector:filter sets for Category Level 3 objects
    def data(self):

        mc = AtlasMetadataCalculator('CategoryLevel1')

        values = list(mc.getHiddenTerms())

        return "var category_1_hidden = %s" % json.dumps(values)

class FieldsetHelp(JSONViewlet):

    title = u"Configuration for help text for the edit form"

    def data(self):

        _ = [
            {
                'selector' : u'#formfield-form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_1',
                'heading' : u'Categories',
                'description' : [
                    u'Categories determine where the product will appear in the navigation of the Extension website. Please select only the relevant categories that apply.',
                ],
            },
            {
                'selector' : u'#formfield-form-widgets-IAtlasProductAttributeMetadata-atlas_language',
                'heading' : u'Attributes',
                'description' : [
                    u'Attributes determine which filter sets a product appears under on the Extension website. They allow an additional dimension for users to narrow the category or search results. Please select only the relevant attributes that apply.',
                ],
            },
            {
                'selector' : u'#formfield-form-widgets-IAtlasEPASMetadata-epas_unit',
                'heading' : u'Extension Activity Reporting',
                'description' : [
                    u'The following values were determined by ADPs and Program Team Leaders and align closely with our organization. The selections for this product are synced to Salesforce for a variety of reporting purposes. Please select the most appropriate value(s) for the product you are creating or updating. Choose one topic set for each product, and up to five for a workshop, webinar or conference.',
                ],
            },
            {
                'selector' : u'body.portaltype-atlas_news_item #formfield-form-widgets-IAtlasCounty-county',
                'heading' : u'County',
                'description' : [
                    u'Select a county or counties on which this News Item should be featured.',
                ],
            },

        ]

        return "var fieldset_help = %s" % json.dumps(_)

class GlobalSectionsViewlet(_GlobalSectionsViewlet, ViewletBase):

    def update(self):
        pass

    @property
    def selected_tabs(self):
        return self.selectedTabs(portal_tabs=self.portal_tabs)

    @property
    def selected_portal_tab(self):
        return self.selected_tabs['portal']

    @property
    def portal_tabs(self):
        context = aq_inner(self.context)
        portal_tabs_view = getMultiAdapter((context, self.request),
                                           name='portal_tabs_view')

        v = portal_tabs_view.topLevelTabs()

        if v:
            v =  v[0:1]

        results = self.portal_catalog.searchResults({'Type' : 'CategoryLevel1', 'sort_on' : 'sortable_title'})

        for r in results:

            # If the 'hide from top nav' checkbox is checked, don't include the
            # L1 in the top nav.

            o = r.getObject()

            hide_from_top_nav = getattr(o, 'hide_from_top_nav', False)

            if not hide_from_top_nav:

                v.append({
                        'url': r.getURL(),
                        'description': r.Description,
                        'name': r.Title.replace(' and ', ' & '), # Shortening title for top nav
                        'id': r.getId,
                    }
                )

        return v

class OtherLocationsViewlet(ViewletBase):

    def show(self):
        return self.show_old or self.show_new

    @property
    def show_old(self):

        if not self.is_admin:
            return False

        original_plone_ids = getattr(self.context, 'original_plone_ids', [])

        if original_plone_ids:
            return (len(original_plone_ids) > 0)

        return False

    @property
    def show_new(self):
        return not not self.new_url

    @property
    def old_url(self):
        return '%s/@@to_old_plone' % self.context.absolute_url()

    @property
    def new_url(self):
        magento_url = getattr(aq_base(self.context), 'magento_url', None)

        if magento_url:
            return u'https://extension.psu.edu/%s' % magento_url

class HistoryViewlet(ContentHistoryViewlet, HistoryByLineView):

    def message_count(self):

        messages = []

        if IVersionable.providedBy(self.context):

            for i in self.fullHistory():
                comments = i.get('comments', '')

                if comments:
                    messages.append(comments)

        return len(messages)

    def show_history(self):

        is_atlas_content = False

        for i in [IAtlasProduct,  IArticleDexterityContent, IArticleDexterityContainedContent]:
            if i.providedBy(self.context):
                is_atlas_content = True
                break

        if is_atlas_content:
            return super(HistoryViewlet, self).show_history()

        return False

# Viewlet that shows a Google Map of a locatable object
class GoogleMapViewlet(ViewletBase):

    @property
    def adapted(self):
        return ILocationMarker(self.context)

    @property
    def api_key(self):
        return self.adapted.api_key

    @property
    def place_id(self):
        return self.adapted.place_id

    @property
    def coords(self):
        return self.adapted.coords

    @property
    def map_url(self):
        return self.adapted.map_url

    @property
    def has_valid_coords(self):
        return self.adapted.has_valid_coords

    @property
    def is_mappable(self):
        return self.adapted.is_mappable

    # Ref: https://developers.google.com/maps/documentation/embed/guide
    @property
    def iframe_url(self):
        q = {}

        api_key = self.api_key

        if api_key:
            q['key'] = api_key

        q['center'] = q['q'] = ",".join(['%0.8f' % x for x in self.coords])

        # If we're mappable, use the place id as the query.
        if self.is_mappable:
            q['q'] = 'place_id:%s' % self.place_id

        q['zoom'] = 16

        return "https://www.google.com/maps/embed/v1/place?%s" % urlencode(q)

# Viewlet that shows an embedded YouTube video
class YouTubeVideoViewlet(ViewletBase):

    @property
    def adapted(self):
        return VideoDataAdapter(self.context)

    @property
    def video_id(self):
        return self.adapted.getVideoId()

    @property
    def has_video(self):
        return not not self.video_id

    @property
    def klass(self):
        return self.adapted.klass

    @property
    def iframe_url(self):
        return self.adapted.iframe_url

# Logo with override if the environment registry key is set.
class LogoViewlet(_LogoViewlet, ViewletBase):

    def environment(self):
        return self.registry.get("agsci.atlas.environment", None)

# Shows a listing of educational drivers for the L2 landing page
class CategoryL2EducationalDriversViewlet(ViewletBase, BaseView):

    def driver_factory(self, d):

        class o(object):
            def __init__(self, d):
                self.title = d.split(DELIMITER)[-1]
                self.objects = []

            def add(self, o):
                self.objects.append(o)

        return o(d)

    def educational_drivers(self):

        l2_metadata = AtlasMetadataCalculator('CategoryLevel2')
        l2 = l2_metadata.getMetadataForObject(self.context)
        drivers = [x.value for x in EducationalDriversVocabularyFactory(self.context) if x.value.startswith(l2)]

        rv = dict([(x, self.driver_factory(x)) for x in drivers])

        results = self.portal_catalog.searchResults({'EducationalDrivers' : drivers})

        for r in results:
            for d in r.EducationalDrivers:
                if d in rv:
                    rv[d].add(r)


        values = [x for x in rv.values() if x.objects]

        return sorted(values, key=lambda x: x.title)


# Base class to shows a listing of featured products for the category landing page
class CategoryFeaturedProductsViewlet(ViewletBase, BaseView):

    # Define level for featured products
    level = 1

    @property
    def category_level(self):
        return 'CategoryLevel%d' % self.level

    @property
    def featured_index(self):
        return 'IsFeaturedProductL%d' % self.level

    @property
    def query(self):

        level_metadata = AtlasMetadataCalculator('CategoryLevel%d' % self.level)
        category_name = level_metadata.getMetadataForObject(self.context)

        return {
            self.category_level : category_name,
            self.featured_index : True,
            'sort_on' : 'sortable_title'
        }

    def products(self):
        return self.portal_catalog.searchResults(self.query)

class CategoryL1FeaturedProductsViewlet(CategoryFeaturedProductsViewlet):
    pass

class CategoryL2FeaturedProductsViewlet(CategoryFeaturedProductsViewlet):
    level = 2

class CategoryL3FeaturedProductsViewlet(CategoryFeaturedProductsViewlet):
    level = 3


# Updated breadcrumbs
class PathBarViewlet(_PathBarViewlet):
    pass

# Shows a link to the related products view
class AtlasRelatedProducts(ViewletBase):

    def show(self):
        return not IsChildProduct(self.context)()

# Shows a link to file downloads for the product, if they exist
class AtlasDownloads(ViewletBase):

    @property
    def download_urls(self):
        return [x for x in self.get_download_urls()]

    def get_download_urls(self):

        # Manual or automaticlly generated PDF downloads for articles
        if IArticle.providedBy(self.context):

            adapted = PDFDownload(self.context)

            if adapted.pdf_file:
                yield object_factory(
                    url='%s/@@download/pdf_file' % self.context.absolute_url(),
                    label="PDF Version",
                )

            elif adapted.pdf_autogenerate:
                yield object_factory(
                    url='%s/@@pdf_download' % self.context.absolute_url(),
                    label="PDF Version (Autogenerated)",
                )
            else:
                yield object_factory(
                    url='%s/@@pdf_download?preview=1' % self.context.absolute_url(),
                    label="Preview Autogenerated PDF Version",
                )

        # ZIP file of curriculum
        elif ICurriculumDigital.providedBy(self.context):

            adapted = CurriculumDataAdapter(self.context)

            if adapted.files:

                yield object_factory(
                    url='%s/@@curriculum_download' % self.context.absolute_url(),
                    label="Curriculum Download (%s total size, ZIP Archive)" % adapted.total_file_size,
                )

                yield object_factory(
                    url='%s/@@outline_preview' % self.context.absolute_url(),
                    label="Curriculum Outline (HTML)",
                )

class ProductPositionsViewlet(ViewletBase):

    def products(self):

        product_positions = getattr(self.context, 'product_positions', [])

        if product_positions:

            data = dict(
                [(x.get('sku', None), x.get('position', None))
                    for x in product_positions ])

            skus = data.keys()

            results = self.portal_catalog.searchResults({
                'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                'SKU' : skus,
            })

            return sorted(results, key=lambda x: data.get(x.SKU, 99999))

class CventWebinarViewlet(ViewletBase):

    @property
    def show(self):
        v = self.context.restrictedTraverse('@@cvent_webinar')
        return not not v.cvent_event

    def post_url(self):
        url = '%s/@@cvent_webinar' % self.context.absolute_url()

        return addTokenToUrl(url)

class CventExternalEventViewlet(ViewletBase):

    @property
    def show(self):
        v = self.context.restrictedTraverse('@@cvent_external_event')
        return not not v.cvent_event

    def post_url(self):
        url = '%s/@@cvent_external_event' % self.context.absolute_url()

        return addTokenToUrl(url)

class CventEventLinkViewlet(ViewletBase):

    @property
    def url(self):
        cvent_id = getattr(self.context, 'cvent_id', None)
        if cvent_id:
            return 'https://app.cvent.com/Subscribers/Events2/Overview/Overview/Index/View?evtstub=%s' % cvent_id

class CSSViewlet(ViewletBase):
    pass
