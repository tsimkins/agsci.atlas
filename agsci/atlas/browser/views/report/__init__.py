from .status import AtlasStatusSummary
from ..helpers import ContentStructure

class UserContentView(AtlasStatusSummary):

    keys = ['review_state', 'Type']
    content_structure_factory = ContentStructure

    def getFolderContents(self, **contentFilter):

        query = {'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                 'sort_on' : 'sortable_title'}

        user_id = self.getCurrentUser()

        if user_id:
            query['Owners'] = user_id

        return self.portal_catalog.searchResults(query)

    def getStatus(self, v):
    
        review_state_view = self.review_state_data.get(v.get('review_state', ''), '')
        
        if review_state_view:
        
            return self.getViewTitle(review_state_view)
        
        return "Unknown"


    def getContentStructure(self, **contentFilter):

        results = self.getFolderContents(**contentFilter)

        v = self.content_structure_factory(self.context, results, self.keys)

        return v()

    def getType(self, brain):
        return brain.Type.lower().replace(' ', '')
