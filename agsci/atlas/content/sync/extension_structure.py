# This provides some methods to create the site IA based on the configuration
# file in agsci.atlas/resources/ia.txt

from zLOG import LOG
from plone.dexterity.utils import createContentInContainer

from agsci.atlas.utilities import ploneify

import json

# Hierarchy of category types
content_types = ['atlas_state_extension_team', 'atlas_program_team',]

# Based on the JSON input file, create the site IA Categories
def createExtensionStructure(context):

    # Traverse to the JSON static configuration
    resource = context.restrictedTraverse('++resource++agsci.atlas/extension_structure.json')

    # Get the config contents
    data = json.loads(resource.GET())

    _id = 'teams'
        
    if _id not in context.objectIds():
        context = createContentInContainer(context, 'Folder', id=_id, title='Teams')
    else:
        context = context[_id]

    createItem(context, data)

# Recursively create categories
def createItem(context, data={}, level=0):

    # Iterate through the data dict
    for k in sorted(data.keys()):
     
        # Get the human readable name, and make it into a short name
        name = k.strip()
        _id = ploneify(name)
        
        # Get the content type for this level
        content_type = content_types[level]

        # If the short name exists, grab the object
        if _id in context.objectIds():
            item = context[_id]
            LOG("agsci.atlas.content.sync.extension_structure.createExtensionStructure", LOG, "Found: %s %s" % (_id, name))

        # Otherwise, create a category under `context`
        else:
            item = createContentInContainer(context, content_type, id=_id, title=name)
            LOG("agsci.atlas.content.sync.extension_structure.createExtensionStructure", LOG, "Created: %s %s" % (_id, name))

        # Get the value for the key
        v = data[k]

        if v:

            # If we have filter sets, assign them to the category
            if isinstance(v, list):
                item.atlas_curriculum = tuple(v)
            else:
                # These are subcategories.  Run this method again at the next level.
                createItem(item, v, level+1)

        LOG("agsci.atlas.content.sync.ia.createIAStructure", LOG, "Finished %s : %s" % (content_type, name))
