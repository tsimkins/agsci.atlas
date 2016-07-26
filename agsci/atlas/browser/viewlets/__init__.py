from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.common import ViewletBase
from plone.dexterity.interfaces import IDexterityEditForm
from plone.dexterity.browser.add import DefaultAddView
from zope.interface.interface import Method
from zope.component import subscribers

from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.content import IAtlasProduct, atlas_schemas
from agsci.atlas.content.check import IContentCheck

import json

class SchemaDump(object):

    def __init__(self, schema, context):
        
        self.schema = schema
        self.context = context
    
    def title(self):
        return self.schema.__name__

    def formatValue(self, x):
        if isinstance(x, (str, unicode)):
            return x
        else:
            return repr(x)

    def hasFields(self):
        return len(self.schema.names()) > 0

    def fieldValues(self):

        for (key, field) in self.schema.namesAndDescriptions():

            if isinstance(field, Method):
                continue

            if hasattr(self.context, key):
                value = getattr(self.context, key)
                
                if not isinstance(value, (list, tuple)):
                    value = [value,]
                
                value = [self.formatValue(x) for x in value if x and not isinstance(x, bool)]
                
                if value:
                    yield(
                        {
                            'name' : field.title,
                            'description' : field.description,
                            'value' : value,
                        }
                    )

class AtlasDataCheck(ViewletBase):

    def data(self):

        for i in subscribers((self.context,), IContentCheck):
            c = i.check()

            if c:
                yield c

class AtlasDataDump(ViewletBase):

    def data(self):

        schema_data = []

        for s in atlas_schemas:

            if s.providedBy(self.context):

                schema_data.append(SchemaDump(s, self.context))

        return schema_data


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