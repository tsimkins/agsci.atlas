from Acquisition import aq_chain
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from zope.security import checkPermission

def onProductPublish(context, event):

    # Don't actually do anything
    return False


# If content is added, removed, moved (renamed) or edited, unpublish the parent
# product.

def onProductCRUD(context, event):

    # Types where editing the product or a child cause the product to back through
    # the review process
    _types = [
        u"App",
        u"Article",
        u"Conference",
        u"Curriculum",
        u"Hyperlink",
        u"Learn Now Video",
        u"News Item",
        u"Online Course",
        u"Program",
        u"Publication",
        u"Smart Sheet",
        u"Video",
        u"Webinar",
        u"Workshop",
        u"Conference Group",
        u"Online Course Group",
        u"Webinar Group",
        u"Workshop Group",
    ]

    for o in aq_chain(event.object):
        if hasattr(o, 'Type'):
            if o.Type() in _types:
                wftool = getToolByName(o, "portal_workflow")
                review_state = wftool.getInfoFor(o, 'review_state').lower()

                # If the product is in a Published state, retract
                if review_state in ['published', ]:

                    # Check if person has reviewer role on context
                    is_reviewer = checkPermission('cmf.ReviewPortalContent', o)

                    # If this person isn't a reviewer, retract it for review.
                    if not is_reviewer:

                        # Comments for transition
                        comments = []

                        # If we're operating on the product, append a simple comment
                        if o.UID() == event.object.UID():

                            # Comment explaining why this was retracted
                            comments.append("Automatically retracted due to editing product.")

                        # If we're operating on product content, be more verbose
                        else:
                            # Comment explaining why this was retracted
                            comments.append("Automatically retracted due to editing content inside product.")

                            # Append any change note from page edit to the product edit.
                            comments.append(getChangeNote(event))

                        comment = ' '.join(comments).strip()

                        # Retract the product
                        wftool.doActionFor(o, 'retract', comment=comment)

                    else:
                        # If the person *is* a reviewer, explicitly set last modified date
                        o.setModificationDate(DateTime())

                    # Reindex.
                    o.reindexObject()
                    o.reindexObjectSecurity() # Not sure if we need this

                else:
                    # Regardless, reindex the product so it recalculates the content checks
                    o.reindexObject(idxs=['ContentIssues',])
                    o.reindexObject(idxs=['ContentErrorCodes'])

                return True

    return False

# If there's a change note with the request, returns the text
def getChangeNote(event):
    return event.object.REQUEST.get('form.widgets.IVersionable.changeNote', '')