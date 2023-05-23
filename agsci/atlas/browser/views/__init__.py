from DateTime import DateTime
from Products.CMFPlone.utils import safe_unicode
from datetime import datetime
from plone.app.layout.globals.layout import LayoutPolicy as _LayoutPolicy
from plone.app.layout.viewlets.content import ContentHistoryView
from plone.app.workflow.browser.sharing import SharingView as _SharingView
from plone.app.workflow.browser.sharing import AUTH_GROUP
from plone.memoize.view import memoize
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory

try:
    from plone.app.search.browser import Search as _SearchView
except ImportError:
    from Products.CMFPlone.browser.search import Search as _SearchView

try:
    from urllib.parse import urlparse # Python 3
except ImportError:
    from urlparse import urlparse # Python 2

from agsci.atlas import object_factory
from agsci.api.api import BaseView as APIBaseView
from agsci.api.api import BaseContainerView as APIBaseContainerView
from agsci.atlas.interfaces import IPDFDownloadMarker
from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DELIMITER
from agsci.atlas.content.behaviors import ILinkStatusReport
from agsci.atlas.content.check import ExternalLinkCheck, InternalLinkCheck, \
                                      ProhibitedWords
from agsci.atlas.content.adapters import CurriculumDataAdapter, VideoDataAdapter, \
    EventGroupPoliciesAdapter

from agsci.atlas.content.adapters.related_products import BaseRelatedProductsAdapter
from agsci.atlas.content.behaviors import IAtlasFilterSets, \
                                          IAtlasProductAttributeMetadata, \
                                          IHomepageTopics, ILinkStatusReportRowSchema
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.events import reindexProductOwner
from agsci.atlas.events.video import getYouTubeChannelAPIData
from agsci.atlas.utilities import generate_sku_regex, SitePeople, encode_blob, get_csv
from agsci.leadimage.content.behaviors import LeadImage

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
            self.request.response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')

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

        # Look for URL parameter 'level' first
        _level = self.request.form.get('level', '')

        if isinstance(_level, (str, unicode)) and _level.isdigit():
            return int(_level) - 1 # (Off by one)

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

class CategoryProductCountCSVView(CategoryProductCountView, APIBaseView):

    default_data_format = 'csv'

    headers = [
        u"Category",
        u"Count",
        u"Count (Active)",
    ]

    def getCSV(self):

        def cols(_):
            return _[0:3]

        return get_csv(
            headers=self.headers,
            data=[x[0:3] for x in self.data]
        )

    @property
    def csv_filename(self):
        return "%s_category_product_count.csv" % datetime.now().strftime('%Y-%m-%d_%H%M%S')

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

class Search(_SearchView):

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

        results = self.portal_catalog.searchResults(
            {
                'object_provides' : [
                    'agsci.atlas.content.IAtlasProduct',
                ]
            }
        )

        def fix_missing_value(_):
            if isinstance(_, bool):
                return _
            return None

        return [
            self.fix_value_datatypes({
                'name' : x.Title,
                'updated_at' : x.modified,
                'plone_url' : x.getURL().replace('http://', 'https://'),
                'plone_id' : x.UID,
                'plone_status' : x.review_state,
                'sku' : x.SKU,
                'plone_product_type' : x.Type,
                'is_external_store' : fix_missing_value(x.IsExternalStore),
                'is_internal_store' : fix_missing_value(x.IsInternalStore),
                'publish_date' : x.effective,
            }) for x in results
        ]


class CategorySKUView(APIBaseView):

    caching_enabled = False

    @property
    def fields(self):
        return ['CategoryLevel%d' % x for x in range(1,4)]

    @property
    def products(self):

        results = self.portal_catalog.searchResults(
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

                    if f not in data:
                        data[f] = {}

                    v = getattr(r, f, [])

                    if v:
                        for j in v:
                            if j not in data[f]:
                                data[f][j] = []
                            data[f][j].append(r.SKU)

        return data

class CategorySKURegexView(CategorySKUView):

    default_data_format = 'csv'

    headers = ["Category Level", "Category", "SKU Regex"]

    def _getData(self, *args, **kwargs):
        data = super(CategorySKURegexView, self)._getData(*args, **kwargs)

        _ = []

        for (level,v) in data.items():
            for (category,skus) in v.items():
                _.append([level, category, self.generate_sku_regex(skus)])

        return sorted(_)

    def getCSV(self):

        return get_csv(
            headers=self.headers,
            data=self.data,
        )

    def generate_sku_regex(self, skus=[]):
        return generate_sku_regex(skus)

class ExternalLinkCheckView(BaseView):

    def set_link_status_report(self, results):

        fields = ILinkStatusReportRowSchema.names()

        link_report = []

        if results:

            for _ in results:
                __ = dict([(x, getattr(_.data, x, '')) for x in fields])
                link_report.append(__)

        setattr(self.context, 'link_report', link_report)
        setattr(self.context, 'link_report_date', datetime.now())

    def link_check(self):
        results = [x for x in ExternalLinkCheck(self.context).manual_check()]
        self.set_link_status_report(results)
        return results

class ExternalLinkCheckReportView(BaseView):

    def klass(self, _):
        v = {
            200 : 'none',
            301 : 'low',
            302 : 'low',
            403 : 'medium',
            404 : 'medium',
        }.get(_.get('status', ''), 'high')

        return 'error-check-%s' % v

    @property
    def products(self):

        # Get active products with links
        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ACTIVE_REVIEW_STATES,
            'ContentErrorCodes' : 'ExternalLinkCheck',
        })

    @property
    def results(self):

        _ = [x for x in self._results if not x.status in (200,)]
        _.sort(key=lambda x: x.brain.Title)
        _.sort(key=lambda x: x.status, reverse=True)

        return _

    @property
    def _results(self):

        for r in self.products:

            o = r.getObject()

            if ILinkStatusReport.providedBy(o):

                link_report = getattr(o, 'link_report', [])
                link_report_date = getattr(o, 'link_report_date', None)

                if link_report_date:

                    link_report_date = link_report_date.strftime('%Y-%m-%d')

                    if link_report:

                        for _ in link_report:
                            yield object_factory(
                                klass=self.klass(_),
                                brain=r,
                                link_report_date=link_report_date,
                                **_
                            )

class PersonExternalLinkCheckReportView(ExternalLinkCheckReportView):

    @property
    def username(self):
        return getattr(self.context, 'username', '')

    @property
    def products(self):

        # Get active products with links
        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ACTIVE_REVIEW_STATES,
            'ContentErrorCodes' : 'ExternalLinkCheck',
            'Owners' : self.username
        })

class PersonReviewQueueView(PersonExternalLinkCheckReportView):

    @property
    def expires_min(self):
        return DateTime() - 6*31

    @property
    def expires_max(self):
        return DateTime() + 6*31

    def is_automatically_expired(self, r):
        if r.review_state in ('expired',):
            o = r.getObject()
            v = ContentHistoryView(o, self.request)
            history = v.workflowHistory()
            history = [x for x in history if x.get('time', None) and x['time'] >= self.expires_min]
            if history:
                actions = [x['action'] for x in history]
                if 'expiring_soon' in actions:
                    expired = [x for x in history if x['state_title'] == 'Expired']
                    if expired:
                        comments = expired[0].get('comments', '')
                        return comments and 'Automatically expired' in comments

    @property
    def products(self):

        # Get active products with links
        expired = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ['expired',],
            'Owners' : self.username,
            'expires' : {
                'range' : 'min',
                'query' : self.expires_min,
            },
            'modified' : {
                'range' : 'min',
                'query' : self.expires_min,
            },
            'sort_on' : 'modified',
        })

        expiring_soon = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ['expiring_soon',],
            'Owners' : self.username,
            'sort_on' : 'expires',
        })

        published = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ['published',],
            'Owners' : self.username,
            'expires' : {
                'range' : 'max',
                'query' : self.expires_max,
            },
            'sort_on' : 'expires',
        })

        expired = [x for x in expired]
        expired.sort(key=lambda x: (x.expires, x.modified))

        expiring_soon = [x for x in expiring_soon]
        expiring_soon.extend([x for x in published])
        expiring_soon.sort(key=lambda x: (x.expires, x.modified))

        results = []
        results.extend(expired)
        results.extend(expiring_soon)


        return results

class DirectoryExternalLinkCheckReportView(ExternalLinkCheckReportView):

    @property
    def results(self):
        results = self.portal_catalog.searchResults({
            'ContentErrorCodes' : 'ExternalLinkCheck',
            'review_state' : ACTIVE_REVIEW_STATES,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
        })

        results = [x for x in results if not x.IsChildProduct]

        owners = []

        for r in results:
            o = r.getObject()
            link_report = getattr(o, 'link_report', None)
            link_report_date = getattr(o, 'link_report_date', None)
            if link_report:
                broken = [x for x in link_report if x.get('status') > 302]
                if broken:
                    owners.extend([x for x in r.Owners if x])

        report = [(owners.count(x), x) for x in set(owners)]

        report.sort(reverse=True)

        sp = SitePeople()

        for (count, owner) in report:
            r = sp.getPersonById(owner)
            if r:
                url = '%s/@@link_check_report' % r.getURL()
                yield object_factory(
                    title=r.Title,
                    count=count,
                    url=url,
                )

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

        results = self.portal_catalog.searchResults(
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
            channel_id = o.getVideoChannel()

            transcript = o.getTranscript()
            has_transcript = not not transcript

            data.append({
                'plone_id' : r.UID,
                'sku' : r.SKU,
                'video_id' : o.getVideoId(),
                'has_transcript' : has_transcript,
                'channel_id' : channel_id,
            })

        return data

class ExpiredProductsView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):

        site_path_length = len(getSite().absolute_url_path())

        data = []

        results = self.portal_catalog.searchResults(
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

        results = self.portal_catalog.searchResults(
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

        results = self.portal_catalog.searchResults(
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

    default_data_format = 'csv'

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

    @property
    def headers(self):
        return [x.replace('_', ' ').title() for x in self.fields]

    def getCSV(self):

        return get_csv(
            headers=self.headers,
            data=self.data,
        )

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

class HiddenProductsView(APIBaseView):

    default_data_format = 'json'

    caching_enabled = False

    @property
    def products(self):
        results = self.portal_catalog.searchResults(
            {
                'object_provides' : [
                    'agsci.atlas.content.IAtlasProduct',
                ],
                'review_state' : ACTIVE_REVIEW_STATES,
            }
        )

        results = [x for x in results if not x.IsChildProduct]
        results = [x for x in results if x.MagentoURL]

        return results

    @property
    def hidden_products(self):
        return [x for x in self.products if x.hide_from_sitemap]

    @property
    def also_hides(self):

        _ = {}

        product_urls = [x.MagentoURL for x in self.products]
        hidden_product_urls = [x.MagentoURL for x in self.hidden_products]

        for url in product_urls:
            for _url in hidden_product_urls:
                if _url != url:
                    if url.startswith(_url):
                        if _url not in _:
                            _[_url] = []
                        _[_url].append(url)

        return _

    def _getData(self, **kwargs):

        also_hides = self.also_hides

        return [
            {
                'plone_id' : x.UID,
                'plone_status' : x.review_state,
                'sku' : x.SKU,
                'plone_product_type' : x.Type,
                'magento_url' : x.MagentoURL,
                'plone_url' : x.getURL(),
                'also_hides' : also_hides.get(x.MagentoURL, [])
            } for x in self.hidden_products
        ]

class RobotsView(HiddenProductsView):

    def __call__(self):
        self.request.response.setHeader('Content-Type', 'text/plain')

        also_hides = self.also_hides
        hidden_products = sorted(self.hidden_products, key=lambda x: x.MagentoURL)

        urls = ["# Start auto-generated robots.txt excludes for hidden products\n"]

        urls.extend(['Disallow: /%s' % x.MagentoURL for x in self.hidden_products if x.MagentoURL and x.MagentoURL not in also_hides.keys()])

        not_hidden = ['# Disallow: /%s' % x.MagentoURL for x in self.hidden_products if x.MagentoURL and x.MagentoURL in also_hides.keys()]

        if not_hidden:
            urls.append("\n# These products are not hidden because another URL starts with this URL.")
            urls.extend(not_hidden)

        urls.append("\n# End auto-generated robots.txt excludes")

        return "\n".join(urls)

class HomeBudgetProgramTeamView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):
        vocabs = [
            "agsci.person.home_budget",
            "agsci.person.project_program_team",
        ]

        _ = {}

        for vocabulary_name in vocabs:
            vocab_key = vocabulary_name.split('.')[-1]
            vocab_factory = getUtility(IVocabularyFactory, vocabulary_name)
            vocab = vocab_factory(self.context)
            _[vocab_key] = [x.value for x in vocab]

        return _

class PersonProgramTeamsView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):

        data = []

        results = self.portal_catalog.searchResults(
            {
                'object_provides' : [
                    'agsci.person.content.person.IPerson',
                ],
                'review_state' : 'published',
            }
        )

        for r in results:

            o = r.getObject()

            fields = [
                'home_budget',
                'project_program_team_percent',
                'delete_project_program_team_percent',
            ]

            _data = dict([
                (x, getattr(o, x, None)) for x in fields
            ])

            if any([x for x in _data.values() if x]):
                _data['sku'] = getattr(o, 'username', r.getId)
                data.append(self.fix_value_datatypes(_data))

        return data

class DepartmentConfigView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    # Check if we're showing binary data
    # Defaults to False
    @property
    def showBinaryData(self):
        v = self.request.form.get('bin', 'False')
        return not (v.lower() in ('false', '0'))

    @property
    def structure(self):
        return {
            'categories' : [],
            'products' : [],
        }

    @property
    def departments(self):
        vocab_factory = getUtility(IVocabularyFactory, 'agsci.atlas.Departments')
        vocab = vocab_factory(self.context)
        return [x.value for x in vocab]

    def get_leadimage(self, r):

        data = {}

        if r.hasLeadImage:

            o = r.getObject()

            img_field_name = 'leadimage'
            img_field = getattr(o, img_field_name, None)

            (img_mimetype, img_data) = encode_blob(img_field, self.showBinaryData)

            leadimage_adapted = LeadImage(o)
            image_extension = leadimage_adapted.image_extension

            # If we DO show binary data
            if self.showBinaryData:

                if img_data:

                    data['leadimage'] = {
                        'data' : img_data,
                        'mimetype' : img_mimetype,
                        'caption' : leadimage_adapted.leadimage_caption,
                    }

            # Set 'thumbnail' URL
            data['filename'] = '%s.%s' % (r.UID, image_extension)
            data['thumbnail'] = '/extension-config/thumbnails/%s' % data['filename']

        return data

    def _getData(self, **kwargs):

        def sort_key(_):
            return (_.get('level', 99999), _.get('name', 'ZZZZZ'))

        # Inside to prevent circular imports
        from agsci.atlas.cron.jobs.magento import MagentoJob

        mj = MagentoJob(self.context)

        # Initialize data structure
        departments = self.departments
        data = dict([(x, self.structure) for x in departments])

        # Get categories
        results = self.portal_catalog.searchResults(
            {
                'object_provides' : [
                    'agsci.atlas.content.structure.IAtlasStructure',
                ],
            }
        )

        for r in results:

            category_name = getattr(r, r.Type, [])

            if category_name and isinstance(category_name, (list, tuple)):
                _c = mj.get_category(category_name[0])

                if _c:

                    if r.hasLeadImage:
                        _c.update(self.get_leadimage(r))

                    if r.Description:
                        _c['description'] = r.Description

                    if r.Departments:
                        for _ in r.Departments:
                            if _ in data:
                                data[_]['categories'].append(_c)

        # Get products
        results = self.portal_catalog.searchResults(
            {
                'object_provides' : [
                    'agsci.atlas.content.IAtlasProduct',
                ],
                'review_state' : ACTIVE_REVIEW_STATES,
            }
        )

        for r in results:

            if r.Departments and r.MagentoURL:

                for _ in r.Departments:

                    if _ in data:

                        _product = mj.by_plone_id(r.UID)

                        if _product:
                            data[_]['products'].append({
                                'name' : r.Title,
                                'description' : r.Description,
                                'url' : 'https://extension.psu.edu/%s' % r.MagentoURL,
                                'product_type' : r.Type,
                                'thumbnail' : _product.get('thumbnail', None),
                                'plone_id' : r.UID,
                                'sku' : r.SKU,
                                'CategoryLevel1' : r.CategoryLevel1,
                                'CategoryLevel2' : r.CategoryLevel2,
                                'CategoryLevel3' : r.CategoryLevel3,
                            })

        for k in data.keys():
            data[k]['categories'].sort(key=lambda x: sort_key(x))
            data[k]['products'].sort(key=lambda x: sort_key(x))

        return data

class YouTubeChannelListingView(APIBaseView):

    caching_enabled = False
    default_data_format = 'json'

    def _getData(self, **kwargs):
        return getYouTubeChannelAPIData()

class CreditsView(BaseView):

    @property
    def data(self):

        data = []

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
            'review_state' : 'published'
        })

        for r in results:

            # Skip if it's not on the site
            if not r.MagentoURL:
                continue

            o = r.getObject()

            credit_type = getattr(o, 'credit_type', [])

            # Skip if there are no credits
            if not credit_type:
                continue

            for _o in o.listFolderContents():

                # Only show published items
                review_state = self.wftool.getInfoFor(_o, 'review_state')

                if review_state not in ['published',]:
                    continue

                # Skip if no SKU
                if not getattr(_o, 'sku', None):
                    continue

                credits = getattr(_o, 'credits', [])

                if credits and _o.start:

                    event_sku = getattr(_o, 'sku', None)

                    _ = {
                        'type' : o.Type(),
                        'title' : o.Title(),
                        'sku' : r.SKU,
                        'event_sku' : event_sku,
                        'url' : 'https://extension.psu.edu/%s' % r.MagentoURL,
                        'start' : _o.start.strftime('%Y-%m-%d'),
                        'end' : _o.start.strftime('%Y-%m-%d'),
                        'credits' : [object_factory(**x) for x in credits],
                    }

                    data.append(object_factory(**_))

        return sorted(data, key=lambda x:(x.title, x.start))

class CheckDetailsView(BaseView):

    check = None

    @property
    def check_name(self):
        if self.check:
            return self.check.__name__

    @property
    def results(self):
        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ACTIVE_REVIEW_STATES,
            'ContentErrorCodes' : self.check_name,
            'sort_on' : 'sortable_title',
        })

    def get_data(self, r, **kwargs):

        _ = {
            'type' : r.Type,
            'title' : r.Title,
            'sku' : r.SKU,
            'url' : r.getURL(),
            'magento_url' : 'https://extension.psu.edu/%s' % r.MagentoURL,
        }

        _.update(kwargs)

        return object_factory(**_)


class ExternalLinksView(CheckDetailsView):

    check = InternalLinkCheck

    @property
    def magento_url_to_product(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ACTIVE_REVIEW_STATES,
        })

        return dict([
            (
                x.MagentoURL,
                object_factory(
                    uid=x.UID,
                    title=x.Title,
                    type=x.Type,
                    magento_url=x.MagentoURL,
                )
            ) for x in results if x.MagentoURL
        ])

    def parse_magento_url(self, url):

        parsed_url = urlparse(url)

        if parsed_url.netloc in ('extension.psu.edu',):
            path = parsed_url.path
            segments = [x for x in path.split('/') if x]
            if segments and len(segments) == 1:
                return segments[0]

    @property
    def data(self):

        magento_url_to_product = self.magento_url_to_product

        data = []

        for r in self.results:

            o = r.getObject()

            c = self.check(o)

            for _c in c.check():

                # Figure out if we're linking to an active product
                target = None

                magento_link_url = self.parse_magento_url(_c.data.url)

                if magento_link_url:
                    target = magento_url_to_product.get(magento_link_url, None)

                _ = self.get_data(r, error=_c, target=target)

                data.append(_)

        return sorted(data, key=lambda x: not x.target)

class ProhibitedWordsView(ExternalLinksView):

    check = ProhibitedWords

    @property
    def data(self):

        data = []

        for r in self.results:

            o = r.getObject()

            c = self.check(o)

            for _c in c.check():

                _ = self.get_data(r, error=_c)

                data.append(_)

        return sorted(data, key=lambda x: x.title)

class PoliciesView(BaseView):

    @property
    def product(self):
        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.behaviors.IEventGroupPolicies',
        })

        if results:
            return results[0].getObject()

    @property
    def policies(self):
        return [x[1] for x in EventGroupPoliciesAdapter(self.product).all_policies]
