from plone.app.event.dx.behaviors import EventAccessor

# Atlas Cvent Event Accessor subclass

class AtlasCventEventAccessor(EventAccessor):
    event_type = 'atlas_cvent_event'

# Factory that takes in product type and returns the correct accessor subclass

def AtlasEventAccessorFactory(product_type):
    return AtlasCventEventAccessor
