from plone.app.layout.globals.layout import LayoutPolicy as _LayoutPolicy
from plone.app.workflow.browser.sharing import SharingView as _SharingView
from plone.app.workflow.browser.sharing import AUTH_GROUP
from plone.memoize.view import memoize

from agsci.atlas.interfaces import IPDFDownloadMarker
from agsci.atlas.constants import ACTIVE_REVIEW_STATES
from agsci.atlas.content import DELIMITER
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

        reindexProductOwner(o, None)

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

# Creates a histogram of products assigned to categories.
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

    # Get the data for the report
    def data(self):

        data = []

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ACTIVE_REVIEW_STATES,
            'IsChildProduct' : False,
        })

        for r in results:

            v = getattr(r, self.content_type, [])

            if v:
                data.extend(v)

        mc = AtlasMetadataCalculator(self.content_type)

        data = [x for x in data if x in mc.getTermsForType()]

        if self.category:
            data = [x for x in data if x.startswith(u'%s%s' % (self.category, DELIMITER))]

        values = [(x, data.count(x), mc.getObjectsForType(x)) for x in set(data)]

        return sorted(values)