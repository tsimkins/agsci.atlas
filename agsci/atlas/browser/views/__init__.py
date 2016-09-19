from agsci.common.browser.views import FolderView
from agsci.atlas.interfaces import IPDFDownloadMarker
from .report.status import AtlasContentStatusView

class PDFDownloadView(FolderView):

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

    # Get the products for this context
    def products(self, contentFilter={}):

        # Construct query to find Atlas Products for this object
        query = {
            'object_provides' : self.product_interface,
            'sort_on' : 'sortable_title',
        }

        query.update(self.context.getQueryForType())

        query.update(self.getOwnersQuery())

        results = self.portal_catalog.searchResults(query)

        results = [x for x in results if x.UID != self.context.UID()]

        return results

    # Return the products as the folder contents
    def getFolderContents(self, contentFilter={}):

        return self.products(**contentFilter)


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