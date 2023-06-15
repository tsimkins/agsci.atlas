from .base import BaseView
from agsci.atlas.content.sync.product import AtlasProductImporter

class OldPloneView(BaseView):

    def __call__(self):

        uid = self.request.form.get('UID', None)

        if not uid:
            raise Exception('UID not provided')

        results = self.portal_catalog.searchResults({'OriginalPloneIds' : uid})

        if not results:
            raise Exception('Old Plone UID %s not found' % uid)

        url = results[0].getURL()

        self.request.response.redirect(url)


class ToOldPloneView(BaseView):

    @property
    def original_plone_ids(self):
        return getattr(self.context, 'original_plone_ids', [])

    @property
    def original_plone_site(self):
        return getattr(self.context, 'original_plone_site', None)

    def __call__(self):

        uids = self.original_plone_ids
        original_plone_site = self.original_plone_site

        if not uids:
            raise Exception('UID not provided')

        for uid in uids:
            v = AtlasProductImporter(uid, domain=original_plone_site)

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
