from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.utilities import ploneify
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite

import transaction

# This runs whenever a category is created. It creates an editors group, and
# assigns Add/Edit
def onCategoryCreate(context, event):

    try:

        mc = AtlasMetadataCalculator(context.Type())

    except ValueError:

        # Not a valid content type
        return

    else:

        # Calculate the group id and title
        title = mc.getMetadataForObject(context)
        group_id = '%s-editors' % ploneify(title)
        group_title = '%s Editors' % title

        # Get the group tool
        site = getSite()
        grouptool = getToolByName(site, 'portal_groups')

        # If our group does not exist, create it and set roles.
        if not grouptool.getGroupById(group_id):

            # Add the new group
            grouptool.addGroup(group_id)

            # Get the group
            group = grouptool.getGroupById(group_id)

            # Set the group title
            group.title = group_title
            group.setGroupProperties({'title' : group_title})

            # Set roles on context
            context.manage_setLocalRoles(group_id, ['Contributor', 'Editor', 'Reader'])
            context.reindexObjectSecurity()

def reindexProductPosition(context, event):

    def adjust_positions(_):
        if isinstance(_, (tuple, list)):
            _ = sorted(_, key=lambda x: x.get('position', 99999))
            
            for i in range (0, len(_)):
                _[i]['position'] = i + 1
            
        return _

    fields = [
        'IProductPositions.product_positions',
    ]

    found = False

    if hasattr(event, 'descriptions'):

        for d in event.descriptions:

            if any([x in fields for x in d.attributes]):
                found = True
                break

    if found:
        product_positions = getattr(context, 'product_positions', [])
        
        if product_positions:
            skus = [x.get('sku', None) for x in product_positions]
            skus = [x for x in skus if x]
            
            portal_catalog = getToolByName(context, 'portal_catalog')
            
            results = portal_catalog.searchResults({
                'SKU' : skus,
                'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            })
            
            for r in results:
                o = r.getObject()
                o.reindexObject()
                transaction.commit()
            
            setattr(context, 'product_positions', adjust_positions(product_positions))