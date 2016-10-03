from agsci.atlas.utilities import ploneify
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite

# This runs whenever a category is created. It creates an editors group, and
# assigns Add/Edit
def onCategoryCreate(context, event):

    # Calculate the group id and title
    title = context.Title()
    group_id = '%s-editors' % ploneify(title)
    group_title = '%s Editors' % title

    # Get the group tool
    site = getSite()
    grouptool = getToolByName(site, 'portal_groups')

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