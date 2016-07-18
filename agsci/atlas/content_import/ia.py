# This provides some methods to create the site IA based on the configuration
# file in agsci.atlas/resources/ia.txt

from Products.CMFCore.utils import getToolByName
from zLOG import LOG, INFO, ERROR
from plone.dexterity.utils import createContentInContainer

from agsci.common import ploneify

import json

# Hierarchy of category types
content_types = ['atlas_category_level_1', 'atlas_category_level_2', 'atlas_category_level_3']

# Based on the JSON input file, create the site IA Categories
def createIAStructure(context):

    # Traverse to the JSON static configuration
    resource = context.restrictedTraverse('++resource++agsci.atlas/ia.json')

    # Get the config contents
    data = json.loads(resource.GET())
    
    createCategory(context, data)

# Recursively create categories
def createCategory(context, data={}, level=0):

    # Iterate through the data dict
    for k in sorted(data.keys()):
        v = data[k]
        
        # If we don't have a value, return
        if not v:
            continue
        
        # Get the human readable name, and make it into a short name
        name = k.strip()
        _id = ploneify(name)
        
        # Get the content type for this level
        content_type = content_types[level]

        # If the short name exists, grab the object
        if _id in context.objectIds():
            item = context[_id]
            LOG("agsci.atlas.content_import.ia.createIAStructure", LOG, "Found: %s %s" % (_id, name))

        # Otherwise, create a category under `context`
        else:
            item = createContentInContainer(context, content_type, id=_id, title=name)
            LOG("agsci.atlas.content_import.ia.createIAStructure", LOG, "Created: %s %s" % (_id, name))
            
        # Set category to not show its own lead image
        item.leadimage_show = False

        # Set category to show images on child objects.
        item.show_image = True

        # If we have filter sets, assign them to the category
        if isinstance(v, list):
            item.atlas_filter_sets = tuple(v)
        else:
            # These are subcategories.  Run this method again at the next level.
            createCategory(item, v, level+1)

        LOG("agsci.atlas.content_import.ia.createIAStructure", LOG, "Finished %s : %s" % (content_type, name))

# Given an object, alphabettically sort the categories inside
def sortChildren(context):

    results = context.listFolderContents({'portal_type' : content_types})
    
    if results:
        results.sort(key=lambda x: x.Title())
        context.moveObjectsToTop([x.getId() for x in results])


# Iterate through all levels of categories (from bottom to top) and sort the
# child categories.  Optionally, clear empty categories.
def fixCategories(context, clear_empty=False):

    portal_catalog = getToolByName(context, "portal_catalog")
    
    for t in reversed(content_types):
        results = portal_catalog.searchResults({'portal_type' : t})
        
        for r in results:
            o = r.getObject()

            sortChildren(o)
            
            if clear_empty:
                if not o.objectIds():
                    LOG("agsci.atlas.content_import.ia.clearEmptyCategories", LOG, "Deleted %s" % o.Title())
                    p = o.aq_parent
                    p.manage_delObjects(ids=[o.getId(), ])
                else:
                    LOG("agsci.atlas.content_import.ia.clearEmptyCategories", LOG, "Kept %s" % o.Title())