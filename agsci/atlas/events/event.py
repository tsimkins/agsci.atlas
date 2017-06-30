from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope.component.hooks import getSite

from agsci.atlas.constants import ACTIVE_REVIEW_STATES
from agsci.atlas.content.event.group import IEventGroup

from . import moveContent
from ..constants import DEFAULT_TIMEZONE

# Run this method when an event is created.
def onEventCreate(context, event):
    pass

# Run this method when an event is modified.
def setExpirationDate(context, event):

    # Set the expiration date to either the end date, or midnight on the start
    # date if it's a multi-day event

    _start = context.start
    _end = context.end

    event_days = (_end - _start).days

    if event_days > 1:
        # Set to midnight of the start date
        context.setExpirationDate(DateTime(_start).toZone(DEFAULT_TIMEZONE).latestTime())
    else:
        # Set to end date
        context.setExpirationDate(DateTime(_end).toZone(DEFAULT_TIMEZONE))

    context.reindexObject()


# Run this method when a Cvent Event is imported
def onCventImport(context, event):

    def _compare(v1, v2):

        def _(x):
            return safe_unicode(x).strip().lower()

        return _(v1) == _(v2)

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
                results = portal_catalog.searchResults({
                    'Type' : parent_type,
                    'review_state' : ACTIVE_REVIEW_STATES,
                })

                # Filter by title
                results = [x for x in results if _compare(x.Title, title)]

                if results:

                    new_parent = results[0].getObject()
                    moveContent(parent, new_parent, context)