from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

def onProductWorkflow(context, event):

    pass

# This runs whenever a product is created or edited
def onProductCreateEdit(context, event):

    # Assign categories and move to category folder
    assignCategoriesAutomatically(context, event)

    # Assign owner permissions
    assignOwnerPermission(context, event)


# Check for content outside of category structure and move it into the correct folder
def assignCategoriesAutomatically(context, event):

    # Get valid category content types
    category_levels = AtlasMetadataCalculator.metadata_content_types

    # Get the parent object
    try:
        parent = context.aq_parent
    except AttributeError:
        return None

    # If the parent is not a category
    if parent.Type() not in category_levels:

        # Go through the category levels in reverse
        for category_level in reversed(category_levels):

            # Get the category value for the current context
            category_value = getattr(context, 'atlas_category_level_%s' % category_level[-1], None)

            # If there's a value for that category at that context, and it's a list/tuple
            if category_value and isinstance(category_value, (list, tuple)):

                # Instantiate a metadata calculator at that level
                mc = AtlasMetadataCalculator(category_level)

                # Get the parent object for the value of that category on the context
                category_parent_objects = mc.getObjectsForType(category_value[0])

                # If there's a parent object (list)
                if category_parent_objects:

                    # Grab the first item in that list
                    new_parent = category_parent_objects[0]

                    # Check the allowed content types for the new parent
                    new_parent_allowed_types = map(lambda x: x.Title(), new_parent.allowedContentTypes())

                    # If our content type is allowed
                    if context.Type() in new_parent_allowed_types:

                        # Move current object to new parent
                        if context.getId() in parent.objectIds():
                            cb_copy_data = parent.manage_cutObjects(ids=[context.getId(),])
                            new_parent.manage_pasteObjects(cb_copy_data=cb_copy_data)

                            # Break out of loop. Our work here is done.
                            break

# Assign owner permissions to object
def assignOwnerPermission(context, event):

    # Get Current Owners from Owners field
    owners = context.owners

    # Get valid owner ids by calculating a set of active person ids and owners
    # field
    portal_catalog = getToolByName(context, 'portal_catalog')

    results = portal_catalog.searchResults({'Type' : 'Person', 'expires' : {'range' : 'min', 'query': DateTime()}})

    all_valid_owner_ids = [x.getId for x in results]

    valid_owner_ids = list(set(owners) & set(all_valid_owner_ids))

    # Add local 'Owner' role for valid owner ids
    for i in valid_owner_ids:

        owner_roles = list(context.get_local_roles_for_userid(i))

        if 'Owner' not in owner_roles:
            owner_roles.append('Owner')
            context.manage_setLocalRoles(i, owner_roles)

    # Remove local Owner roles for non-owners
    for (user, roles) in context.get_local_roles():
        if roles == ('Owner',) and user not in valid_owner_ids:
            context.manage_delLocalRoles([user])

    # Reindex the object and the object security
    context.reindexObjectSecurity()
    context.reindexObject()