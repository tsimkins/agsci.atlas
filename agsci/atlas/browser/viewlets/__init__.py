from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.common import ViewletBase as _ViewletBase
from plone.app.layout.viewlets.common import GlobalSectionsViewlet as _GlobalSectionsViewlet
from plone.app.layout.viewlets.content import DocumentBylineViewlet as _DocumentBylineViewlet
from plone.app.layout.viewlets.content import ContentHistoryViewlet
from plone.dexterity.interfaces import IDexterityEditForm
from plone.dexterity.browser.add import DefaultAddView
from plone.namedfile.file import NamedBlobFile
from zope.interface.interface import Method

from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.content import IAtlasProduct,  IArticleDexterityContent, \
                                IArticleDexterityContainedContent, atlas_schemas
from agsci.atlas.content.check import getValidationErrors

from agsci.atlas.utilities import getAllSchemas as _getAllSchemas

from Acquisition import aq_base, aq_inner
from zope.component import getMultiAdapter

import json

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


class SchemaDump(object):

    def __init__(self, schema, context):

        self.schema = schema
        self.context = context

    def title(self):
        doc_string = getattr(self.schema, '__doc__', None)

        if doc_string:
            return doc_string

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

        return len(self.fieldNames()) > 0

    def fieldNames(self):

        names = []

        for schema in self.getAllSchemas():
            names.extend(schema.names())

        return names

    def getAllSchemas(self, schema=None):

        # If none is provided, use the object for this schema dump
        if not schema:
            schema = self.schema

        return _getAllSchemas(schema)

    def fieldValues(self):

        for schema in set(self.getAllSchemas()):

            for (key, field) in schema.namesAndDescriptions():

                if isinstance(field, Method):
                    continue

                if hasattr(self.context, key):
                    value = getattr(self.context, key)

                    if not isinstance(value, (list, tuple)):
                        value = [value,]

                    value = [self.formatValue(x, key) for x in value if x and not isinstance(x, bool)]

                    if value:
                        yield(
                            {
                                'name' : field.title,
                                'description' : field.description,
                                'value' : value,
                            }
                        )

class AtlasDataCheck(ViewletBase):

    def data(self):
        return getValidationErrors(self.context)

    def post_url(self):
        url = '%s/@@rescan' % self.context.absolute_url()

        return addTokenToUrl(url)


class AtlasDataDump(ViewletBase):

    def data(self):

        schema_data = []

        for schema in atlas_schemas:

            if schema.providedBy(self.context):

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

        fmt = "#formfield-form-widgets-IAtlasProductMetadata-%s"

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