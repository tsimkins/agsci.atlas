from agsci.common.browser.views import FolderView
from agsci.atlas.content.sync.product import AtlasProductImporter

class OldPloneView(FolderView):

    def __call__(self):

        uid = self.request.form.get('UID', None)

        if not uid:
            raise Exception('UID not provided')

        results = self.portal_catalog.searchResults({'OriginalPloneIds' : uid})

        if not results:
            raise Exception('Old Plone UID %s not found' % uid)

        url = results[0].getURL()

        self.request.response.redirect(url)


class ToOldPloneView(FolderView):

    @property
    def original_plone_ids(self):
        return getattr(self.context, 'original_plone_ids', [])

    def __call__(self):

        uids = self.original_plone_ids

        if not uids:
            raise Exception('UID not provided')

        for uid in uids:
            v = AtlasProductImporter(uid)

            try:
                url = v.data.url
            except:
                pass
            else:
                if url:
                    url = url.replace('http://', 'https://')
                    self.request.response.redirect(url)
                    return True

        raise Exception("Could not find content in old Plone site")