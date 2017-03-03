from Products.CMFCore.utils import getToolByName
from agsci.atlas.content.event.group import IEventGroup
from zope.component.hooks import getSite
from Products.CMFPlone.utils import safe_unicode

from . import moveContent

# Run this method when an event is created.
def onEventCreate(context, event):
    pass

# Run this method when a Cvent Event is imported
def onCventImport(context, event):

    # Get the parent object
    try:
        parent = context.aq_parent

    except AttributeError:
        return None

    else:
        # Check to see if parent is a group product.  If it's not, try to find
        # one to move it into.
        if not IEventGroup.providedBy(parent):

        	# Get the event type from the Cvent event.
            event_type = getattr(context, 'atlas_event_type', None)
            title = getattr(context, 'title', None)

            if event_type and title:

                # Get the site and portal_catalog
                site = getSite()
                portal_catalog = getToolByName(site, 'portal_catalog')

                # Find a parent group product with the same type and title as the event
                parent_type = '%s Group' % event_type

                # Catalog query by type, no title (Unicode string matching issues)
                results = portal_catalog.searchResults({'Type' : parent_type})

                # Filter by title
                results = [x for x in results if safe_unicode(x.Title) == safe_unicode(title)]

                if results:

                    new_parent = results[0].getObject()
                    moveContent(parent, new_parent, context)