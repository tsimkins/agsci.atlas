from Products.CMFCore.utils import getToolByName
from agsci.atlas.content.online_course.group import IOnlineCourseGroup
from zope.component.hooks import getSite
from Products.CMFPlone.utils import safe_unicode

from . import moveContent

# Run this method when a Cvent Event is imported
def onOnlineCourseImport(context, event):

    # Get the parent object
    try:
        parent = context.aq_parent

    except AttributeError:
        return None

    else:
        # Check to see if parent is a group product.  If it's not, try to find
        # one to move it into.
        if not IOnlineCourseGroup.providedBy(parent):

        	# Get the title from the online course.
            title = getattr(context, 'title', None)

            if title:

                # Get the site and portal_catalog
                site = getSite()
                portal_catalog = getToolByName(site, 'portal_catalog')

                # Find a parent group product with the same type and title as the event
                parent_type = 'Online Course Group'

                # Catalog query by type, no title (Unicode string matching issues)
                results = portal_catalog.searchResults({'Type' : parent_type})

                # Filter by title
                results = [x for x in results if safe_unicode(x.Title) == safe_unicode(title)]

                if results:

                    new_parent = results[0].getObject()
                    moveContent(parent, new_parent, context)