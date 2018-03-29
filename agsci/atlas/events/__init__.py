from DateTime import DateTime
from Products.CMFDefault.exceptions import ResourceLockedError

from agsci.atlas.utilities import execute_under_special_role, SitePeople
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator

from agsci.person.content.person import IPerson
from ..constants import DEFAULT_TIMEZONE
from ..content import IAtlasProduct

# Move Content method, executed under a special role

def moveContent(parent, new_parent, context):

    def _moveContent(parent, new_parent, context):

        if context.getId() in parent.objectIds():

            # Check the allowed content types for the new parent
            new_parent_allowed_types = map(lambda x: x.Title(), new_parent.allowedContentTypes())

            # If our content type is allowed
            if context.Type() in new_parent_allowed_types:

                # If the object is locked, clear the lock so we can move it.
                if context.wl_isLocked():
                    context.wl_clearLocks()

                # Try moving it to the new location.  If the "cut" still fails
                # due to the resource being locked, just swallow the error.
                try:
                    cb_copy_data = parent.manage_cutObjects(ids=[context.getId(),])
                except ResourceLockedError:
                    pass
                else:
                    new_parent.manage_pasteObjects(cb_copy_data=cb_copy_data)

    # Run the actual move under roles with additional privilege
    execute_under_special_role(['Contributor', 'Reader', 'Editor'],
                                _moveContent, parent, new_parent, context)

def onProductWorkflow(context, event):

    # Move to category folder
    moveToCategoryContainer(context, event)

# This runs whenever a product is created or edited
def onProductCreateEdit(context, event):

    # Assign categories and move to category folder
    moveToCategoryContainer(context, event)

    # Assign owner permissions
    assignOwnerPermission(context, event)

    # Reindex the product owner so we can recalculate the issue summary
    reindexProductOwner(context, event)


# Check for content outside of category structure and move it into the correct folder
def moveToCategoryContainer(context, event):

    # Check the request to make sure this is not being triggered by an import
    try:
        request_url = context.REQUEST.getURL()
    except:
        # Can't get the URL, don't do anything
        return None
    else:
        # If the URL contains '@@import', abort.
        if '@@import_' in request_url:
            return None

    # Get the parent object
    try:
        parent = context.aq_parent
    except AttributeError:
        return None

    # If the parent is a product (e.g. a Workshop Group) return None.
    if IAtlasProduct.providedBy(parent):
        return None

    # Get valid category content types
    category_levels = AtlasMetadataCalculator.metadata_content_types

    # Gets the category value for the object.
    # Level is a *str* of 'CategoryLevel1..3'
    def get_category_value(context, level):

        # Calculate field
        field = 'atlas_category_level_%s' % level[-1]

        # Get field
        value = getattr(context, field, [])

        # Only return value if it's a list/tuple
        if isinstance(value, (list, tuple)):
            return value

        return []

    def get_category_objects(category_level, category_value):
        # Instantiate a metadata calculator at that level
        mc = AtlasMetadataCalculator(category_level)

        # Get the object(s) for the value(s) of that category on the context
        objects = []

        for i in category_value:
            objects.extend(mc.getObjectsForType(i))

        return objects

    # Should we move content?
    move_product = False
    parent_type = parent.Type()

    # If the parent type is not a category
    if parent_type not in category_levels:
        move_product = True

    else:
        # Get the Lx value of the object
        category_value = get_category_value(context, parent_type)

        # Get the object(s) for the parent Lx category value
        category_parent_objects = get_category_objects(parent_type, category_value)

        # Check if the current parent is one of the assigned categories.  If not,
        # we need to move it.
        if parent.UID() not in [x.UID() for x in category_parent_objects]:
            move_product = True

    # If we need to move the product
    if move_product:

        # Go through the category levels in reverse
        for category_level in reversed(category_levels):

            # Get the category value for the current context
            category_value = get_category_value(context, category_level)

            # If there's a value for that category on the context
            if category_value:

                # Get the parent object(s) for that category
                category_parent_objects = get_category_objects(category_level, category_value)

                # If there's a parent object (list)
                if category_parent_objects:

                    # Grab the first item in that list
                    new_parent = category_parent_objects[0]

                    # Move current object to new parent
                    moveContent(parent, new_parent, context)

                    # Break out of loop. Our work here is done.
                    break

# Assign owner permissions to object
def assignOwnerPermission(context, event):

    owners = getOwners(context)

    if not owners:
        return

    # Get valid owner ids by calculating a set of active person ids and owners
    # field

    sp = SitePeople(active=False)
    all_valid_owner_ids = sp.getValidPeopleIds()

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


# Reindex the product owner so we can recalculate the issue summary
def reindexProductOwner(context, event):

    owners = getOwners(context)
    sp = SitePeople(active=False)

    if not owners:
        return

    for i in owners:
        person = sp.getPersonById(i)

        if person:
            person.getObject().reindexObject()

# Get the "owners" field for an object
def getOwners(context):

    # If this is a person, and they have a username return [username,]
    if IPerson.providedBy(context):

        username = getattr(context, 'username', None)

        if username:
            return [username,]

        return []


    # Get Current Owners from Owners field
    try:
        return context.owners
    except AttributeError:
        # No owners defined
        return []

# Workflow actions for news items
def onNewsItemWorkflow(context, event):

    # If the expiration date is not set when the item is published, set it to
    # now plus one year.

    try:
        transition_id = event.transition.getId()
    except AttributeError:
        transition_id = None

    if transition_id in ['publish',]:

        if not context.expiration_date:
            _expiration_date = DateTime() + 365
            context.setExpirationDate(_expiration_date.toZone(DEFAULT_TIMEZONE).latestTime())