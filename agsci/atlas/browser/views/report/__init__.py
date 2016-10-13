from .status import AtlasStatusSummary
from ..helpers import ContentStructure

class UserContentView(AtlasStatusSummary):

    keys = ['review_state', 'Type']
    content_structure_factory = ContentStructure

    def getFolderContents(self, **contentFilter):

        query = self.getBaseProductQuery()

        query.update(self.getOwnersQuery())

        return self.portal_catalog.searchResults(query)

    def getContentStructure(self, **contentFilter):

        results = self.getFolderContents(**contentFilter)

        v = self.content_structure_factory(self.context, results, self.keys)

        return v()

    def getType(self, brain):
        return brain.Type.lower().replace(' ', '')

    def getOwnersQuery(self):

        user_id = self.getCurrentUser()

        if user_id:
            return {'Owners' : user_id}

        return {}