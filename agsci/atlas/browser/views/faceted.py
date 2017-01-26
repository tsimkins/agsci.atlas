from eea.facetednavigation.browser.app.query import FacetedQueryHandler
from . import AtlasStructureView
class AtlasStructureFacetedQueryHandler(AtlasStructureView, FacetedQueryHandler):
    
    def criteria(self, sort=False, **kwargs):
        query = self.getProductQuery()
        faceted_query = super( AtlasStructureFacetedQueryHandler, self).criteria(sort, **kwargs)
        query.update(faceted_query)
        return query