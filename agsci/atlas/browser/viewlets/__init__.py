from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.common import ViewletBase
import json
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator

from plone.dexterity.interfaces import IDexterityEditForm

class Category3AttributeSets(ViewletBase):

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    # Determine if this is an edit form.
    def show(self):
        return IDexterityEditForm.providedBy(self.view)

    def data(self):

        values = {}
        
        results = self.portal_catalog.searchResults({'Type' : 'CategoryLevel3'})

        mc = AtlasMetadataCalculator('CategoryLevel3')

        for r in results:
            o = r.getObject()

            k = mc.getMetadataForObject(o)
            v = getattr(o, 'atlas_filter_sets', [])

            values[k] = v

        return "var category_3_attribute_sets = %s" % json.dumps(values)