from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope.component.hooks import getSite

from agsci.atlas.constants import ACTIVE_REVIEW_STATES
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.interfaces import IWebinarMarker
from agsci.atlas.utilities import localize

from . import moveContent
from ..constants import DEFAULT_TIMEZONE

import transaction

# Run this method when an event is created.
def onEventCreate(context, event):
    pass

# Run this method when an event is modified.
def setExpirationDate(context, event):

    # First, check if it's a webinar.  If it is, and it has a recording inside,
    # remove any existing expiration date and return.
    if context.Type() in ['Webinar',]:
        if IWebinarMarker(context).getPages():
            context.setExpirationDate(None)
            return

    # Calculate a flag for Cvent webinars.
    is_cvent_webinar = False

    if context.Type() in ['Cvent Event',]:

        event_type = getattr(context, 'atlas_event_type', None)

        if event_type in ['Webinar',]:
            is_cvent_webinar = True

    # Set the expiration date to either the end date, or midnight on the start
    # date if it's a multi-day event

    _start = context.start
    _end = context.end

    event_days = (_end - _start).days

    if event_days > 1 and not is_cvent_webinar:

        # We have a special case where, if the registration deadline is after
        # the start date for multi-day events, the event shouldn't expire until
        # the deadline
        _expiration_date = _start

        _deadline = getattr(context, 'registration_deadline', None)

        if _deadline:
            _deadline = localize(_deadline)

            if _deadline > _start:

                # Not sure why the deadline would be after the end, but this
                # seems like a good thing to check.
                if _deadline > _end:
                    _expiration_date = _end

                else:
                    _expiration_date = _deadline

        # Set to midnight of the start date
        context.setExpirationDate(DateTime(_expiration_date).toZone(DEFAULT_TIMEZONE).latestTime())
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

# Run this method when a parent group product (e.g. Workshoup Group) is updated
def onParentGroupUpdate(context, event):

    # Look for updates on EPAS fields
    fields = (
        'IAtlasEPASMetadata.epas_unit',
        'IAtlasEPASMetadata.epas_team',
        'IAtlasEPASMetadata.epas_topic',
        'IAtlasEPASMetadata.epas_primary_team',
    )

    found = False

    if hasattr(event, 'descriptions'):

        for d in event.descriptions:

            if any([x in fields for x in d.attributes]):
                found = True
                break

    if found:

        # Update the modified date on the child objects
        for o in context.listFolderContents():
            o.reindexObject()
            transaction.commit()