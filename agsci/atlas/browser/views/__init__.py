from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from RestrictedPython.Utilities import same_type as _same_type
from RestrictedPython.Utilities import test as _test
from plone.app.workflow.browser.sharing import SharingView as _SharingView
from plone.app.workflow.browser.sharing import AUTH_GROUP
from plone.event.interfaces import IEvent
from plone.memoize.view import memoize
from zope.component import getUtility, getMultiAdapter
from zope.interface import implements, Interface

from agsci.atlas.interfaces import IPDFDownloadMarker
from agsci.atlas.content.behaviors.container import ITileFolder
from agsci.atlas.events import reindexProductOwner
from agsci.leadimage.interfaces import ILeadImageMarker as ILeadImage

from .base import BaseView
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
    def products(self, contentFilter={}):

        return self.getResults()

    # Return the products as the folder contents
    def getFolderContents(self, contentFilter={}):

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

    @memoize
    def role_settings(self):
        current_settings = super(SharingView, self).role_settings()

        site_url = getSite().absolute_url()

        for g in current_settings:
            if g['id'] != AUTH_GROUP and g['type'] == 'group':
                g['group_url'] = "%s/@@usergroup-groupmembership?groupname=%s" % (site_url, g['id'])

        return current_settings

class CountyView(BaseView):
    pass