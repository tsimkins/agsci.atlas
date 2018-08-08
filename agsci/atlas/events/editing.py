from Acquisition import aq_chain
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.container.interfaces import IContainerModifiedEvent
from zope.security import checkPermission
from zope.security.interfaces import NoInteraction

from agsci.atlas.indexer import IsChildProduct
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.content import IAtlasProduct

def onProductPublish(context, event):

    # Don't actually do anything
    return False


# If content is added, removed, moved (renamed) or edited, unpublish the parent
# product.

def onProductCRUD(context, event):

    # If the event group container was modified by adding a child product, ignore.
    if IEventGroup.providedBy(context) and IContainerModifiedEvent.providedBy(event):
        return False

    # Check if this object is a child product
    is_child_product = IsChildProduct(context)()

    # Get the portal_workflow tool
    wftool = getToolByName(context, "portal_workflow")

    # Iterate up through the acquisition chain
    for o in aq_chain(event.object):

        # Break out if we've made it up to the Plone site.
        if IPloneSiteRoot.providedBy(o):
            break

        # If the item in the aq_chain is a product.
        # If our parent is a product defined as a product
        if IAtlasProduct.providedBy(o):

            try:
                review_state = wftool.getInfoFor(o, 'review_state').lower()

            except WorkflowException:
                review_state = ''

            # If the object that triggered the event is a child product, just
            # reindex the item in the chain.
            if is_child_product:
                o.reindexObject()

            # Otherwise, if the product is in a Published state, retract
            elif review_state in ['published', 'expiring_soon']:

                # Check if person has reviewer role on context
                try:
                    is_reviewer = checkPermission('cmf.ReviewPortalContent', o)

                except NoInteraction:
                    # If we're running this through a script, just assume
                    # we can review.
                    is_reviewer = True

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