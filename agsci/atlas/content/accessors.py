from plone.app.event.dx.behaviors import EventAccessor

# Atlas Complex Event Accessor subclass

class AtlasComplexEventAccessor(EventAccessor):

    pass

# Accessor subclass for complex workshop event
class AtlasComplexWorkshopAccessor(AtlasComplexEventAccessor):
    event_type = 'atlas_complex_workshop'

# Factory that takes in product type and returns the correct accessor subclass
# Currently just returns the complex workshop
def AtlasEventAccessorFactory(product_type):
    return AtlasComplexWorkshopAccessor