from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.common import ViewletBase
from plone.dexterity.interfaces import IDexterityEditForm
from plone.dexterity.browser.add import DefaultAddView

from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.content import IAtlasProduct

import json



class Category3AttributeSets(ViewletBase):

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    # Determine if this is an edit or an add form.
    def show(self):
        if IAtlasProduct.providedBy(self.context) and IDexterityEditForm.providedBy(self.view):
            return True
        else:
            return isinstance(self.view, DefaultAddView)

    # Get a JSON output of a dict of CSS selector:filter sets for Category Level 3 objects
    def data(self):

        fmt = "#formfield-form-widgets-IAtlasProductMetadata-%s"

        values = {}
        
        results = self.portal_catalog.searchResults({'Type' : 'CategoryLevel3'})

        mc = AtlasMetadataCalculator('CategoryLevel3')

        for r in results:
            o = r.getObject()

            k = mc.getMetadataForObject(o)
            v = getattr(o, 'atlas_filter_sets', [])
            
            if v:
                values[k] = map(lambda x: fmt % x, v)

        return "var category_3_attribute_sets = %s" % json.dumps(values)