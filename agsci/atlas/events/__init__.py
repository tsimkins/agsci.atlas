from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator

def onProductWorkflow(context, event):
    
    pass

def onProductCreateEdit(context, event):

    # Check for content outside of category structure and move it into the correct folder

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
                        cb_copy_data = parent.manage_cutObjects(ids=[context.getId(),])
                        new_parent.manage_pasteObjects(cb_copy_data=cb_copy_data)

                        # Break out of loop. Our work here is done.
                        break
    
    
