from Acquisition import aq_chain
from Products.CMFCore.utils import getToolByName

# If content is added, removed, moved (renamed) or edited, unpublish the parent 
# article.
    
def onArticleContentCRUD(context, event):

    for o in aq_chain(event.object):
        if hasattr(o, 'Type'):
            if o.Type() in ['Article', ]:
                wftool = getToolByName(o, "portal_workflow")
                review_state = wftool.getInfoFor(o, 'review_state').lower()
                
                if review_state in ['published', ]:
                    wftool.doActionFor(o, 'retract')
                    o.reindexObject()
                    o.reindexObjectSecurity() # Not sure if we need this
                    return True
    return False