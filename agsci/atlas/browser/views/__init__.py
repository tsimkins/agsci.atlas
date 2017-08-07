from plone.app.layout.globals.layout import LayoutPolicy as _LayoutPolicy
from plone.app.workflow.browser.sharing import SharingView as _SharingView
from plone.app.workflow.browser.sharing import AUTH_GROUP
from plone.memoize.view import memoize

from agsci.atlas.interfaces import IPDFDownloadMarker
from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DELIMITER
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.events import reindexProductOwner

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

    def getCategories(self):
        return self.portal_catalog.searchResults({'Type' : 'CategoryLevel1',
                                                  'sort_on' : 'sortable_title'})

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

        reindexProductOwner(self.context, None)

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

            def addCategory(self, name):
                self.children[len(name)].append(Category(name))

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

            def __init__(self, name):
                self.name = name
                self.children = []

            def addCategory(self, c):
                self.children.append(c)

            @property
            def html(self):
                v = []
                v.append(u'<li>')
                v.append(self.name[-1])

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

            terms = [tuple(x.value.split(DELIMITER)) for x in mc.getTermsForType()]

            for t in terms:
                categories.addCategory(t)

        categories.assignChildren()

        return categories.html