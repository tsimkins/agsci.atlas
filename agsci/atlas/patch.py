from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent


# This patch adds an 'update' method to the EventAccessor class.  The 'edit`
# method of this class only updates values in **kwargs that are in the
# _behavior_map dict.  The purpose of this method is to set the attribute value
# for anything that's *not* in that dict.

def event_accessor_update(self, **kwargs):

    bm = self._behavior_map

    for key, value in kwargs.items():
        if key not in bm:
            setattr(self.context, key, value)

    notify(ObjectModifiedEvent(self.context))