from Products.CMFPlone.utils import safe_unicode
from plone.app.layout.globals.layout import LayoutPolicy as _LayoutPolicy
from plone.app.search.browser import Search as _Search
from plone.app.workflow.browser.sharing import SharingView as _SharingView
from plone.app.workflow.browser.sharing import AUTH_GROUP
from plone.memoize.view import memoize
from urlparse import urlparse
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory

from agsci.atlas import object_factory
from agsci.api.api import BaseView as APIBaseView
from agsci.api.api import BaseContainerView as APIBaseContainerView
from agsci.atlas.interfaces import IPDFDownloadMarker
from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DELIMITER
from agsci.atlas.content.check import ExternalLinkCheck
from agsci.atlas.content.adapters import CurriculumDataAdapter, VideoDataAdapter
from agsci.atlas.content.adapters.related_products import BaseRelatedProductsAdapter
from agsci.atlas.content.behaviors import IAtlasFilterSets, \
                                          IAtlasProductAttributeMetadata, \
                                          IHomepageTopics
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.events import reindexProductOwner
from agsci.atlas.utilities import generate_sku_regex

from .base import BaseView
from .product import ProductView
from .report.status import AtlasContentStatusView

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

class PDFDownloadView(BaseView):

    def __call__(self):

        # If we're an anonymous user, and getPDF errors, send an email, and
        # return a boring and unhelpful error message.  If we're logged in, let
        # the error happen.

        if self.anonymous:

            try:
                (pdf, filename) = IPDFDownloadMarker(self.context).getPDF()
            except:
                # Send email
                #emailUsers = ['webservices@ag.psu.edu']
                emailUsers = ['trs22@psu.edu']
                mFrom = "do.not.reply@psu.edu"
                mSubj = "Error auto-generating PDF: %s" % self.context.Title()
                mMsg = '<p><strong>ERROR:</strong> <a href="%s">%s</a></p>'  % (self.context.absolute_url(), self.context.Title())
                mailHost = self.context.MailHost

                for mTo in emailUsers:
                    mailHost.secureSend(mMsg.encode('utf-8'), mto=mTo, mfrom=mFrom, subject=mSubj, subtype='html')

                # Return error message
                return "<h1>Error</h1><p>Sorry, an error has occurred.</p>"

        else:
            (pdf, filename) = IPDFDownloadMarker(self.context).getPDF()

        if pdf:
            self.request.response.setHeader('Content-Type', 'application/pdf')
            self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % filename)

            return pdf

        return "<h1>Error</h1><p>No PDF download available.</p>"

# Download of zipped curriculum files
class DigitalCurriculumZipFileView(BaseView):

    def __call__(self):

        adapted = CurriculumDataAdapter(self.context)

        zip_file = adapted.zip_file

        if zip_file:
            self.request.response.setHeader('Content-Type', 'application/zip')
            self.request.response.setHeader(
                'Content-Disposition', 'attachment; filename="%s"' % adapted.zip_file_filename
            )

            return zip_file

        return "<h1>Error</h1><p>No ZIP file download available.</p>"

class AtlasStructureView(AtlasContentStatusView):

    product_interface = 'agsci.atlas.content.IAtlasProduct'
    review_state = None

    # Get the products for this context
    def products(self, **contentFilter):

        return self.getResults(**contentFilter)

    # Return the products as the folder contents
    def getFolderContents(self, **contentFilter):

        return self.products(**contentFilter)

    # Don't show child products
    def getChildProductQuery(self):

        return {'IsChildProduct' : False}


class ExtensionStructureView(AtlasStructureView):

    pass


class PloneSiteView(AtlasContentStatusView):

    def mc(self, content_type):
        return AtlasMetadataCalculator(content_type)

    def getCategories(self):
        mc = self.mc(u'CategoryLevel1')
        return mc.getObjectsForType()

    def getTeams(self):
        return self.portal_catalog.searchResults({'Type' : 'StateExtensionTeam',
                                                  'sort_on' : 'sortable_title'})
    def getDirectories(self):
        return self.portal_catalog.searchResults({'Type' : 'Directory',
                                                  'sort_on' : 'sortable_title'})

    # Filter out 'view' default view for Plone Site
    def navigation_items(self):
        items = super(PloneSiteView, self).navigation_items()
        return [x for x in items if x[-1] != 'view']

class ProductListingView(AtlasContentStatusView):

    pass

class ReindexObjectView(BaseView):

    def __call__(self):

        path = '/'.join(self.context.getPhysicalPath())
        results = self.portal_catalog.searchResults({'path' : path})

        for r in results:
            o = r.getObject()
            o.reindexObject()

        # Send an ObjectModifiedEvent
        notify(ObjectModifiedEvent(self.context))

        return self.request.response.redirect('%s?rescanned=1' % self.context.absolute_url())

class SharingView(_SharingView):

    def update(self):
        super(SharingView, self).update()
        self.request.set('disable_plone.rightcolumn',1)
        self.request.set('disable_plone.leftcolumn',1)

    def roles(self):

        # We're going to push all of our custom roles off to the right.

        def sort_order(v):

            items = [
                         u'Event Group Editor',
                         u'Cvent Editor',
                         u'Online Course Editor',
                         u'Publication Editor',
                         u'Video Editor',
                         u'Site Administrator',
                    ]

            try:
                return items.index(v) + 1
            except ValueError:
                return 0

        roles = super(SharingView, self).roles()
        roles.sort(key=lambda x: sort_order(x.get('id')))

        return roles

    @memoize
    def role_settings(self):
        current_settings = super(SharingView, self).role_settings()

        site_url = getSite().absolute_url()

        for g in current_settings:
            if g['id'] != AUTH_GROUP and g['type'] == 'group':
                g['group_url'] = "%s/@@usergroup-groupmembership?groupname=%s" % (site_url, g['id'])

        return current_settings

# Overriding layout policy
class LayoutPolicy(_LayoutPolicy, BaseView):

    def bodyClass(self, template, view):

        body_class = super(LayoutPolicy, self).bodyClass(template, view)

        # If we're an alternate environment, append a class to the body tag
        alternate_environment = self.registry.get("agsci.atlas.environment", None)

        if alternate_environment:
            body_class += " alternate-environment"

        return body_class

# Creates a table of products assigned to categories.
class CategoryProductCountView(ProductView):

    # Category content types
    content_types = ['CategoryLevel1', 'CategoryLevel2', 'CategoryLevel3']

    # URL 'category' parameter
    @property
    def category(self):
        return self.request.form.get('category', '')

    # Index for the category level in the listing
    @property
    def level(self):
        c = self.category

        if c:
            return c.count(DELIMITER) + 1

        return 0

    # Current content type, based on the level
    @property
    def content_type(self):
        return self.content_types[self.level]

    # Don't show links for the last level
    def show_link(self):
        return self.level < len(self.content_types) - 1

    # The view name
    def view_name(self):
        return '@@%s' % self.__name__

    # Query the catalog
    @property
    def results(self):
        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'IsChildProduct' : False,
        })

    # Metadata Calculator
    @property
    def mc(self):
        return AtlasMetadataCalculator(self.content_type)

    # Get the data for the report
    @property
    def data(self):

        # Data structures
        data = []
        active_data = []

        # Metadata for categories
        mc = self.mc
        terms = mc.getTermsForType()

        # Iterate through results, and compile categories
        for r in self.results:

            v = getattr(r, self.content_type, [])

            # If the object has categories
            if v:
                # Filter out invalid categories
                v = [x for x in v if x in terms]

                # Push onto the data list
                data.extend(v)

                # If the review state is active, track this separately.
                if r.review_state in ACTIVE_REVIEW_STATES:
                    active_data.extend(v)

        # If we were given a category in the URL, filter the results by that category
        if self.category:
            data = [x for x in data if x.startswith(u'%s%s' % (self.category, DELIMITER))]

        values = [(x, data.count(x), active_data.count(x), mc.getObjectsForType(x)) for x in set(data)]

        return sorted(values)

# Creates a table of number of categories assigned to a product
class CategoryCountView(CategoryProductCountView):

    # URL 'level' parameter. Default to 0 (really, L1)
    @property
    def level(self):
        try:
            return int(self.request.form.get('level', 0))
        except:
            return 0

    # URL 'count' parameter. Default to 0
    @property
    def count(self):
        try:
            return int(self.request.form.get('count', 0))
        except:
            return 0

    # URL 'active' parameter. Default to False
    @property
    def active(self):
        try:
            not not self.request.form.get('active', 'false').lower() in ['false', '0']
        except:
            return False

    # Get the data for the report
    @property
    def data(self):

        # Data structures
        category_brains = []
        data = []
        active_data = []

        # Metadata for categories
        mc = self.mc
        terms = mc.getTermsForType()

        # Iterate through results, and compile categories
        for r in self.results:

            v = getattr(r, self.content_type, [])

            # If the object has categories
            if v:

                # Filter out invalid categories
                v = [x for x in v if x in terms]

                # Push onto the data list
                category_brains.append((v, r))

        category_keys = set([len(x[0]) for x in category_brains])

        data = dict([(x, []) for x in category_keys])
        active_data = dict([(x, []) for x in category_keys])

        for (v, r) in category_brains:
            k = len(v)

            data[k].append(r)

            # If the review state is active, track this separately.
            if r.review_state in ACTIVE_REVIEW_STATES:
                active_data[k].append(r)

        values = [(x, data.get(x, []), active_data.get(x, [])) for x in sorted(category_keys)]

        return values

    # Get the detail for the report
    def detail(self):

        data = self.data

        rv = []

        v = [x for x in data if x[0] == self.count]

        if v:

            v = v[0]

            if self.active:
                rv = v[2]

            rv = v[1]

        rv.sort(key=lambda x: (x.Type, x.Title))

        return rv

class InformationArchitecture(BaseView):

    def html(self):

        class Categories(object):

            levels = 3

            def __init__(self):
                self.children = dict([(x, []) for x in range(1,self.levels+1)])

            def addCategory(self, name, url):
                self.children[len(name)].append(Category(name, url))

            def assignChildren(self):

                for i in range(1,self.levels):

                    for c in self.children[i]:
                        _children = [x for x in self.children[i+1] if tuple(x.name[0:i]) == c.name]

                        for _c in _children:
                            c.addCategory(_c)
            @property
            def html(self):

                v = []
                v.append(u'<ul>')

                for c in self.children[1]:
                    v.extend(c.html)

                v.append(u'</ul>')

                return "\n".join(v)

        class Category(object):

            def __init__(self, name, url):
                self.name = name
                self.url = url
                self.children = []

            def addCategory(self, c):
                self.children.append(c)

            @property
            def html(self):
                v = []
                v.append(u'<li>')

                v.append(u'<a href="%s">' % self.url)
                v.append(self.name[-1])
                v.append(u'</a>')

                if self.children:

                    v.append(u'<ul>')

                    for c in self.children:
                        v.extend(c.html)

                    v.append(u'</ul>')

                v.append(u'</li>')

                return v

        categories = Categories()

        for i in range(1,4):

            mc = AtlasMetadataCalculator('CategoryLevel%d' % i)

            terms = [x.value for x in mc.getTermsForType()]

            for t in terms:

                url = mc.getObjectsForType(t, objects=False)[0].getURL()
                _t = tuple(t.split(DELIMITER))

                categories.addCategory(_t, url)

        categories.assignChildren()

        return categories.html

class Search(_Search):

    # When we search, only return products or people
    def filter_query(self, query):
        query = super(Search, self).filter_query(query)

        query['object_provides'] = [
            'agsci.atlas.content.IAtlasProduct',
            'agsci.person.content.person.IPerson',
        ]

        return query

class ProductStatusView(APIBaseView):

    caching_enabled = False

    def _getData(self, **kwargs):

        results = self.portal_catalog.queryCatalog(
            {
                'object_provides' : [
                    'agsci.atlas.content.IAtlasProduct',
                ]
            }
        )

        return [
            {
                'plone_id' : x.UID,
                'plone_status' : x.review_state,
                'sku' : x.SKU,
                'plone_product_type' : x.Type,
            } for x in results
        ]

class CategorySKUView(APIBaseView):

    caching_enabled = False

    @property
    def fields(self):
        return ['CategoryLevel%d' % x for x in range(1,4)]

    @property
    def products(self):

        results = self.portal_catalog.queryCatalog(
            {
                'object_provides' : [
                    'agsci.atlas.content.IAtlasProduct',
                ],
            }
        )

        return [x for x in results if not x.IsChildProduct]

    def _getData(self, **kwargs):

        data = {}

        for r in self.products:

            if r.SKU:

                for f in self.fields:

                    if not data.has_key(f):
                        data[f] = {}

                    v = getattr(r, f, [])

                    if v:
                        for j in v:
                            if not data[f].has_key(j):
                                data[f][j] = []
                            data[f][j].append(r.SKU)

        return data

class CategorySKURegexView(CategorySKUView):

    default_data_format = 'tsv'

    headers = ["Category Level", "Category", "SKU Regex"]

    def _getData(self, *args, **kwargs):
        data = super(CategorySKURegexView, self)._getData(*args, **kwargs)

        _ = []

        for (level,v) in data.iteritems():
            for (category,skus) in v.iteritems():
                _.append([level, category, self.generate_sku_regex(skus)])

        return sorted(_)

    def getTSV(self):

        def cols(_):
            return u"\t".join([safe_unicode(x) for x in _])

        data = self.data

        data.insert(0, self.headers)

        _ = u"\n".join([cols(x) for x in data])

        return _.encode('utf-8')

    def generate_sku_regex(self, skus=[]):
        return generate_sku_regex(skus)

class ExternalLinkCheckView(BaseView):

    def link_check(self):
        return [x for x in ExternalLinkCheck(self.context).manual_check()]

class RelatedProductListingView(ProductListingView):

    def query_by_sku(self, skus=[], **contentFilter):

        def key(x):
            try:
                return skus.index(x)
            except:
                return 99999

        query = {
            'SKU' : skus,
            'sort_on' : 'sortable_title',
        }

        query.update(contentFilter)

        return sorted(self.portal_catalog.searchResults(query), key=lambda x: key(x.SKU))

    # Return the products as the folder contents
    def getFolderContents(self, **contentFilter):

        adapted = BaseRelatedProductsAdapter(self.context)

        related_skus = adapted.related_skus
        secondary_related_skus = adapted.secondary_related_skus(related_skus=related_skus)

        for (title, skus) in [
            ('Related Products', related_skus),
            ('Secondary Related Products', secondary_related_skus),
        ]:
            results = self.query_by_sku(skus, **contentFilter)
            yield object_factory(title=title, results=results)

class FiltersView(BaseView):

    @property
    def filter_sets(self):

        # List of catalog indexes
        indexes = self.portal_catalog.indexes()

        _ = []

        for _iface in (IAtlasProductAttributeMetadata, IAtlasFilterSets, IHomepageTopics):

            for (_name, _description) in  _iface.namesAndDescriptions():

                # Only display indexed fields
                if _name not in indexes:
                    continue

                options = []

                try:
                    vocabulary_name = _description.value_type.vocabularyName
                except:
                    # Skip fields with no vocabulary
                    continue
                else:
                    vocab_factory = getUtility(IVocabularyFactory, vocabulary_name)
                    vocab = vocab_factory(self.context)
                    options = [x.value for x in vocab]

                _.append(
                    object_factory(
                        field=_name,
                        title=_description.title,
                        options=options,
                    )
                )

        return sorted(_, key=lambda x: x.title)

    def products(self, field, options):

        query = {
            'object_provides' : [
                'agsci.atlas.content.IAtlasProduct',
            ],
            'review_state' : 'published',
        }

        query[field] = options

        return self.portal_catalog.searchResults(query)

class VideoTranscriptsView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):

        data = []

        results = self.portal_catalog.queryCatalog(
            {
                'object_provides' : [
                    'agsci.atlas.content.video.IVideo',
                ],
                'review_state' : 'published',
            }
        )

        for r in results:

            o = VideoDataAdapter(r.getObject())

            video_id = o.getVideoId()
            plone_id = r.UID

            transcript = o.getTranscript()
            has_transcript = not not transcript

            data.append({
                'plone_id' : r.UID,
                'video_id' : o.getVideoId(),
                'has_transcript' : has_transcript,
            })

        return data

class ExpiredProductsView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):

        site_path_length = len(getSite().absolute_url_path())

        data = []

        results = self.portal_catalog.queryCatalog(
            {
                'object_provides' : [
                    'agsci.atlas.content.IAtlasProduct',
                ],
                'review_state' : 'expired',
            }
        )

        # Filter out child products
        results = [x for x in results if not x.IsChildProduct]

        # Only show items with a Magento URL
        results = [x for x in results if x.MagentoURL]

        for r in results:

            o = r.getObject()
            adapted = BaseRelatedProductsAdapter(o)

            _structure = []

            for _ in adapted.all_parent_categories:

                hide_from_top_nav = getattr(_, 'hide_from_top_nav', False)

                if not hide_from_top_nav:

                    _level = _.Type()[-1]
                    _url = _.absolute_url_path()[site_path_length:]

                    _structure.append({
                        'url' : _url,
                        'level' : _level
                    })

            if _structure:

                _data = {
                    'structure' : _structure,
                    'magento_url' : r.MagentoURL,
                    'plone_id' : r.UID,
                    'plone_product_type' : r.Type,
                }

                data.append(_data)

        return data

class HyperlinkURLsView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):

        data = []

        results = self.portal_catalog.queryCatalog(
            {
                'object_provides' : [
                    'agsci.atlas.content.program.IProgramLink',
                ],
                'review_state' : 'published',
            }
        )

        for r in results:

            o = r.getObject()
            external_url = getattr(o, 'external_url', None)

            if external_url and r.MagentoURL:
                data.append({
                    'magento_url' : r.MagentoURL,
                    'external_url' : external_url,
                })

        return data

class CategoryURLView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):
        return sorted([x for x in self.links], key=lambda x: (x['type'], x['title']))

    @property
    def links(self):

        results = self.portal_catalog.queryCatalog(
            {
                'object_provides' : [
                    'agsci.atlas.content.structure.IAtlasStructure',
                ],
            }
        )

        site_path = "/".join(self.context.getPhysicalPath())

        for r in results:

            o = r.getObject()
            mc = AtlasMetadataCalculator(r.Type)
            title = mc.getMetadataForObject(o)

            url = "/".join(o.getPhysicalPath())

            parsed_url = urlparse(url)
            path = parsed_url.path[len(site_path):]
            path = 'https://extension.psu.edu%s' % path

            yield ({
                'type' : r.Type,
                'title' : title,
                'url' : path,
            })

class CountyExportView(APIBaseView):

    caching_enabled = False

    default_data_format = 'tsv'

    fields = [
        'name',
        'address',
        'city',
        'state',
        'zip',
        'email_address',
        'office_hours',
        'phone',
        'fax',
        'latitude',
        'longitude',
        'magento_url',
    ]

    def _getData(self, *args, **kwargs):

        rv = []

        if 'counties' in self.context.objectIds():

            context = self.context['counties']

            v = APIBaseContainerView(context, self.request)

            data = v.getData()

            for _ in data.get('contents', []):

                if _.get('plone_product_type', '') in ('County',):

                    rv.append([_.get(x, '') for x in self.fields])

        return sorted(rv)

    def getTSV(self):

        def fmt(_):

            if isinstance(_, (list, tuple)):
                return "; ".join(_)

            return _

        def cols(_):
            return u"\t".join([safe_unicode(fmt(x)) for x in _])

        data = self.data

        data.insert(0, [x.replace('_', ' ').title() for x in self.fields])

        _ = u"\n".join([cols(x) for x in data])

        return _.encode('utf-8')

class EPASSKUView(CategorySKUView):

    default_data_format = 'json'

    fields = [
        'EPASUnit',
        'EPASTeam',
        'EPASTopic',
    ]

    headers = ["EPAS Level", "Value", "SKU Regex"]

class EPASSKURegexView(EPASSKUView, CategorySKURegexView):

    pass