from Acquisition import aq_base, aq_chain
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from bs4 import BeautifulSoup
from plone.app.textfield.value import RichTextValue
from zope.container.interfaces import IContainerModifiedEvent
from zope.security import checkPermission
from zope.security.interfaces import NoInteraction

try:
    from plone.base.interfaces.siteroot import ISiteRoot
except ImportError:
    from Products.CMFPlone.interfaces.siteroot import ISiteRoot

from agsci.atlas.browser.views import ExternalLinksView
from agsci.atlas.indexer import IsChildProduct
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.content import IAtlasProduct
from agsci.atlas.content.check import InternalLinkCheck
from agsci.atlas.utilities import zope_log


def is_reviewer(context):
    # Check if person has reviewer role on context
    try:
        return checkPermission('cmf.ReviewPortalContent', context)

    except NoInteraction:
        # If we're running this through a script, just assume
        # we can review.
        return True

def get_current_user_id(context):
    membership_tool = getToolByName(context, 'portal_membership', None)
    if membership_tool:
        member = membership_tool.getAuthenticatedMember()
        if member:
            user_id = member.getId()
            if user_id:
                return user_id
        

def onProductPublish(context, event):
    zope_log('onProductPublish %s' % context.absolute_url())
    # Don't actually do anything
    return False

def onProductReview(context, event):
    zope_log('onProductReview %s' % context.absolute_url())
    # Don't actually do anything
    if event.action in ('under_review') and is_reviewer(context):
        user_id = get_current_user_id(context)
        if user_id:
            setattr(context.aq_base, 'web_team_reviewer', [user_id,])
            context.reindexObject()
    elif event.action in ('archived', 'expired', 'publish', 'retract',):
        user_id = get_current_user_id(context)
        if user_id:
            setattr(context.aq_base, 'web_team_reviewer', [])
            context.reindexObject()
            
# If content is added, removed, moved (renamed) or edited, unpublish the parent
# product.

def onProductCRUD(context, event):
    zope_log('onProductCRUD %s' % context.absolute_url())

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
        if ISiteRoot.providedBy(o):
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

                # If this person isn't a reviewer, retract it for review.
                if not is_reviewer(o):

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

# Sets the primary EPAS Team if only one EPAS Team is selected
def setPrimaryEPASTeam(context, event):
    zope_log('setPrimaryEPASTeam %s' % context.absolute_url())
    _context = aq_base(context)

    epas_primary_team = getattr(_context, 'epas_primary_team', None)
    epas_team = getattr(_context, 'epas_team', None)

    # If a team is provided.
    if epas_team:

        # Just set the primary team if the value for the team(s) has only one value.
        if len(epas_team) == 1:
            setattr(_context, 'epas_primary_team', epas_team[0])

        # Otherwise, if multiple teams are selected, and the primary team isn't
        # one of them, blank out the primary team.
        else:
            if epas_primary_team and epas_primary_team not in epas_team:
                setattr(_context, 'epas_primary_team', None)

def autoFixExternalLinks(context, event):
    replacements = {}
    check = InternalLinkCheck(context)
    errors = [x for x in check.check()]
    magento_urls = [x.data.url for x in errors if x.data.url]
    if errors:
        elv = ExternalLinksView(context, event.object.REQUEST)
        m2_product_urls = elv.get_magento_urls_to_products(magento_urls)
        for _ in errors:
            href = _.data.url
            if href:
                m2_url = elv.parse_magento_url(href)
                if m2_url:
                    product_record = m2_product_urls.get(m2_url)
                    if product_record:
                        plone_uid = product_record.uid
                        if plone_uid:
                            replacements[href] = plone_uid
    if replacements:
        text = getattr(context.aq_base, 'text', None)
        if text and hasattr(text, 'raw') and text.raw:
            update_html = False
            html = text.raw
            soup = BeautifulSoup(html, features="lxml")
            for a in soup.findAll('a'):
                href = a.get('href', None)
                if href and href in replacements:
                    plone_uid = replacements.get(href)
                    if plone_uid:
                        update_html = True
                        a['href'] = f'resolveuid/{plone_uid}'
                        a['data-linktype'] = 'internal'
                        a['data-val'] = plone_uid
            if update_html:
                soup.html.unwrap()
                soup.body.unwrap()
                new_html = str(soup)
                context.text = RichTextValue(
                    raw=new_html,
                    mimeType=u'text/html',
                    outputMimeType='text/x-html-safe'
                )