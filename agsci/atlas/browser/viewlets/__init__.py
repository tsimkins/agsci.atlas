
from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.common import GlobalSectionsViewlet as _GlobalSectionsViewlet
from plone.app.layout.viewlets.common import LogoViewlet as _LogoViewlet
from plone.app.layout.viewlets.common import ViewletBase as _ViewletBase
from plone.app.layout.viewlets.content import ContentHistoryViewlet
from plone.app.layout.viewlets.content import DocumentBylineViewlet as _DocumentBylineViewlet
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.interfaces import IDexterityEditForm
from plone.namedfile.file import NamedBlobFile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.interface.interface import Method

from agsci.atlas.content.vocabulary import EducationalDriversVocabularyFactory
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.content import IAtlasProduct,  IArticleDexterityContent, \
                                IArticleDexterityContainedContent, atlas_schemas, \
                                DELIMITER
from agsci.atlas.content.adapters import VideoDataAdapter
from agsci.atlas.content.check import getValidationErrors

from agsci.atlas.interfaces import ILocationMarker

from agsci.atlas.utilities import getBaseSchema, getAllSchemaFieldsAndDescriptions

from Acquisition import aq_inner
from zope.component import getMultiAdapter

from ..views import BaseView

import json
import urllib

try:
    from plone.protect.utils import addTokenToUrl
except ImportError:
    def addTokenToUrl(x):
        return x

class ViewletBase(_ViewletBase):

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
        if isinstance(x, (str, unicode)):
            return x
        elif isinstance(x, (NamedBlobFile,)):
            url = '%s/@@download/%s' % (self.context.absolute_url(), key)
            return '<a href="%s">%s</a>' % (url, url)
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

                if not isinstance(value, (list, tuple)):
                    value = [value,]

                value = [self.formatValue(x, key) for x in value if x and not isinstance(x, bool)]

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

        schema_data = []

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


class Category3AttributeSets(ViewletBase):

    # Determine if this is an edit or an add form.
    def show(self):
        if IAtlasProduct.providedBy(self.context) and IDexterityEditForm.providedBy(self.view):
            return True
        else:
            return isinstance(self.view, DefaultAddView)

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
                values[k] = map(lambda x: fmt % x, v)

        return "var category_3_attribute_sets = %s" % json.dumps(values)

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
            v.append({
                    'url': r.getURL(),
                    'description': r.Description,
                    'name': r.Title.replace(' and ', ' & '), # Shortening title for top nav
                    'id': r.getId,
                }
            )

        return v

class OldLocationViewlet(ViewletBase):

    def show(self):
        original_plone_ids = getattr(self.context, 'original_plone_ids', [])

        if original_plone_ids:
            return (len(original_plone_ids) > 0)

        return False

    def old_url(self):
        return '%s/@@to_old_plone' % self.context.absolute_url()


class DocumentBylineViewlet(_DocumentBylineViewlet, ContentHistoryViewlet):

    def message_count(self):

        messages = []

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
            return super(DocumentBylineViewlet, self).show_history()

        return False

# Viewlet that shows a Google Map of a locatable object
class GoogleMapViewlet(ViewletBase):

    @property
    def coords(self):
        return ILocationMarker(self.context).coords

    @property
    def has_valid_coords(self):
        return ILocationMarker(self.context).has_valid_coords

    # Ref: https://developers.google.com/maps/documentation/embed/guide
    @property
    def iframe_url(self):
        q = {}

        api_key = ILocationMarker(self.context).api_key

        if api_key:
            q['key'] = api_key

        q['center'] = q['q'] = ",".join(['%0.8f' % x for x in self.coords])
        q['zoom'] = 16

        return "https://www.google.com/maps/embed/v1/place?%s" % urllib.urlencode(q)

# Viewlet that shows an embedded YouTube video
class YouTubeVideoViewlet(ViewletBase):

    @property
    def video_id(self):
        return VideoDataAdapter(self.context).getVideoId()

    @property
    def has_video(self):
        return not not self.video_id

    @property
    def klass(self):
        k = ['youtube-video-embed']

        aspect_ratio = VideoDataAdapter(self.context).getVideoAspectRatio()

        if aspect_ratio:
            k.append('aspect-%s' % aspect_ratio.replace(':', '-'))

        return " ".join(k)

    @property
    def iframe_url(self):
        return "https://www.youtube.com/embed/%s" % self.video_id

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
                if rv.has_key(d):
                    rv[d].add(r)


        values = [x for x in rv.values() if x.objects]
        
        return sorted(values, key=lambda x: x.title)

# Shows a listing of featured products for the L2 landing page
class CategoryL2FeaturedProductsViewlet(ViewletBase, BaseView):

    def products(self):

        l2_metadata = AtlasMetadataCalculator('CategoryLevel2')
        l2 = l2_metadata.getMetadataForObject(self.context)

        return self.portal_catalog.searchResults({'CategoryLevel2' : l2,
                                                  'IsFeaturedProduct' : True,
                                                  'sort_on' : 'sortable_title'})