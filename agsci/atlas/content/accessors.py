from plone.app.event.dx.behaviors import EventAccessor

# Atlas Cvent Event Accessor subclass
class AtlasCventEventAccessor(EventAccessor):
    event_type = 'atlas_cvent_event'

# Atlas Webinar Accessor subclass
class AtlasWebinarAccessor(EventAccessor):
    event_type = 'atlas_webinar'

# Factory that takes in product type and returns the correct accessor subclass
# Note: The value for `product_type` is .Type(), not .portal_type
def AtlasEventAccessorFactory(product_type):

    if product_type in ('Cvent Event'):
        return AtlasCventEventAccessor

    elif product_type in ('Webinar'):
        return AtlasWebinarAccessor

    return EventAccessor