from Acquisition import aq_chain
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName

import requests

def onArticlePublish(context, event):

    # Don't actually do anything
    return False


# If content is added, removed, moved (renamed) or edited, unpublish the parent
# article.

def onArticleContentCRUD(context, event):

    for o in aq_chain(event.object):
        if hasattr(o, 'Type'):
            if o.Type() in ['Article', ]:
                wftool = getToolByName(o, "portal_workflow")
                review_state = wftool.getInfoFor(o, 'review_state').lower()

                # If the article is in a Published state, retract
                if review_state in ['published', ]:

                    # Comment explaining why this was retracted
                    comments = ["Automatically retracted due to editing content inside article."]

                    # Append any change note from page edit to the article edit.
                    comments.append(getChangeNote(event))

                    comment = ' '.join(comments).strip()

                    wftool.doActionFor(o, 'retract', comment=comment)
                    
                    o.reindexObject()
                    o.reindexObjectSecurity() # Not sure if we need this

                else:
                    # Regardless, reindex the article so it recalculates the content checks
                    o.reindexObject(idxs=['ContentIssues',])
                    o.reindexObject(idxs=['ContentErrorCodes'])

                return True

    return False

# If there's a change note with the request, returns the text
def getChangeNote(event):
    return event.object.REQUEST.get('form.widgets.IVersionable.changeNote', '')