from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.utilities import ploneify
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite

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