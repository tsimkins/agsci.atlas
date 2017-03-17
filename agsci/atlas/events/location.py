from ..interfaces import ILocationMarker

# Actions taken when an object with a location is saved
def onLocationProductCreateEdit(context, event, force=False):

    # Adapt the context for location
    context = ILocationMarker(context)

    # If we're forcing, or if we don't have values, get them and set them on the
    # object.  'has_coords' considers values of (0,0) as "valid" (e.g. "Don't
    # look this up again.)
    #
    # OR, if the address is updated.
    if force or not context.has_coords or context.is_address_updated(event):

        (lat, lng) = context.lookup_coords()

        if lat and lng:
            context.set_coords(lat, lng)