from Products.CMFPlone.utils import safe_unicode

from . import CronJob

class ExpireExpiredProducts(CronJob):

    title = "Expire published products that have an expiration date in the past."

    def run(self):
    
        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'expires' : {
                'range' : 'max',
                'query' : self.now,
            },
            'review_state' : 'published',
        })
        
        msg = "Automatically expired based on expiration date."
        
        for r in results:
            o = r.getObject()
            
            self.portal_workflow.doActionFor(o, 'expired', comment=msg)
            o.reindexObject()
            
            self.log(u"Expired %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

class DeactivateExpiredPeople(CronJob):

    title = "Deactivate active people that have an expiration date in the past."

    def run(self):
    
        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.person.content.person.IPerson',
            'expires' : {
                'range' : 'max',
                'query' : self.now,
            },
            'review_state' : 'published',
        })

        msg = "Automatically deactivated based on expiration date."
        
        for r in results:
            o = r.getObject()
            
            self.portal_workflow.doActionFor(o, 'deactivate', comment=msg)
            o.reindexObject()
            
            self.log(u"Deactivated %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))