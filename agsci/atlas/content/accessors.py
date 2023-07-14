from plone.app.event.dx.behaviors import EventAccessor as _EventAccessor
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

class EventAccessor(_EventAccessor):

    # .create() and .edit() methods copied from v 1.2.x since they were (apparently?) remmoved

    # Unified create method via Accessor
    @classmethod
    def create(cls, container, content_id, title, description=None,
               start=None, end=None, timezone=None,
               whole_day=None, open_end=None, **kwargs):
        container.invokeFactory(cls.event_type,
                                id=content_id,
                                title=title,
                                description=description,
                                start=start,
                                end=end,
                                whole_day=whole_day,
                                open_end=open_end,
                                timezone=timezone)
        content = container[content_id]
        acc = cls(content)
        acc.edit(**kwargs)
        return acc

    def edit(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        notify(ObjectModifiedEvent(self.context))

# Atlas Cvent Event Accessor subclass
class AtlasCventEventAccessor(EventAccessor):
    event_type = 'atlas_cvent_event'

# Atlas Webinar Accessor subclass
class AtlasWebinarAccessor(EventAccessor):
    event_type = 'atlas_webinar'

# Atlas External Event Accessor subclass
class AtlasExternalEventAccessor(EventAccessor):
    event_type = 'atlas_external_event'

# Factory that takes in product type and returns the correct accessor subclass
# Note: The value for `product_type` is .Type(), not .portal_type
def AtlasEventAccessorFactory(product_type):

    if product_type in ('Cvent Event'):
        return AtlasCventEventAccessor

    elif product_type in ('Webinar'):
        return AtlasWebinarAccessor

    elif product_type in ('External Event'):
        return AtlasExternalEventAccessor

    return EventAccessor
