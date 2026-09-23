from Acquisition import aq_chain
from plone.dexterity.browser.edit import DefaultEditForm, DefaultEditView
from plone.dexterity.interfaces import IDexterityEditForm
from zope.interface import implementer
from Products.CMFCore.utils import getToolByName
from zope.security import checkPermission
from plone.z3cform import layout
from zope.interface import classImplements

from agsci.atlas.content.behaviors import IAtlasWebTeamReviewer
from agsci.atlas.content import IAtlasProduct

import logging

try:
    from plone.base.interfaces.siteroot import ISiteRoot
except ImportError:
    from Products.CMFPlone.interfaces.siteroot import ISiteRoot

logger = logging.getLogger(__name__)

@implementer(IDexterityEditForm)
class ProductEditForm(DefaultEditForm):

    """
    Custom edit form that fires when the form loads (before save).
    Override the update() method which is called when the form is displayed.
    """

    def update(self):
        """
        This method is called when the edit form initially loads,
        before the user submits the form.
        """
        # Call the parent update() to proceed with normal form initialization
        super(ProductEditForm, self).update()

        # Perform custom actions when form loads
        self.handle_form_load()

    def updateFields(self):
        super(ProductEditForm, self).updateFields()
        # custom field tweaks here, AFTER calling super()

    def updateWidgets(self):
        super(ProductEditForm, self).updateWidgets()
        # custom widget tweaks here, AFTER calling super()
        # (self.groups is only populated once super() has run)

    def is_reviewer(self, context):
        # Check if person has reviewer role on context
        try:
            return checkPermission('cmf.ReviewPortalContent', self.context)

        except NoInteraction:
            # If we're running this through a script, just assume
            # we can review.
            return True

    def is_pending(self, context):
        return self.wftool.getInfoFor(context, 'review_state') in ('pending',)

    @property
    def wftool(self):
        return getToolByName(self.context, 'portal_workflow')

    @property
    def portal_membership(self):
        return getToolByName(self.context, 'portal_membership')

    @property
    def user_id(self):
        member = self.portal_membership.getAuthenticatedMember()
        if member:
            return member.getUserId()

    @property
    def product(self):
        # Traverse up until we hit product or a Plone site
        # Iterate up through the acquisition chain
        for o in aq_chain(self.context):

            # Break out if we've made it up to the Plone site.
            if ISiteRoot.providedBy(o):
                break

            # If the item in the aq_chain is a product.
            # If our parent is a product defined as a product
            if IAtlasProduct.providedBy(o):
                return(o)

    def handle_form_load(self):
        request_url = self.request.getURL()

        # Skip Widget URLs
        if '++widget++' in request_url:
            return

        product = self.product
        user_id = self.user_id

        if product and user_id:
            logger.info(f"Edit form loaded for: (Title: {product.Title()})")

            # Example: Pre-populate form data, set defaults, log form access
            logger.info(f"User is editing: {product.absolute_url()}")

            if IAtlasWebTeamReviewer.providedBy(product) and \
               self.is_reviewer(product) and \
               self.is_pending(product):

                # Change the status
                self.wftool.doActionFor(product, 'under_review', comment=f"{user_id} started editing.")

                # Set reviewer
                setattr(product.aq_base, 'web_team_reviewer', [user_id,])
                product.reindexObject()

class ProductEditView(DefaultEditView):
    form = ProductEditForm
