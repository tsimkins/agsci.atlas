from agsci.common.browser.views import FolderView
from ..helpers import ContentStructure

class UserContentView(FolderView):

    keys = ['review_state', 'Type']
    content_structure_factory = ContentStructure

    def getFolderContents(self, **contentFilter):

        query = {'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                 'sort_on' : 'sortable_title'}

        user_id = self.getUserId()

        if user_id:
            query['Owners'] = user_id

        return self.portal_catalog.searchResults(query)

    def getContentStructure(self, **contentFilter):

        results = self.getFolderContents(**contentFilter)

        v = self.content_structure_factory(self.context, results, self.keys)

        return v()

    def getType(self, brain):
        return brain.Type.lower().replace(' ', '')

    def getIssues(self, brain):
        issues = brain.ContentIssues

        levels = ['High', 'Medium', 'Low']

        if issues:
            rv = []

            data = dict(zip(levels, issues))

            for k in levels:
                v = data.get(k)

                if isinstance(v, int) and v > 0:
                    rv.append(v*('<span class="error-check-%s"></span>' % k.lower()))
            if rv:
                return "".join(rv)

            return '<span class="error-check-none"></span>'


class AllContentView(UserContentView):

    keys = ['Type', 'review_state']

    def getUserId(self):

        return None

