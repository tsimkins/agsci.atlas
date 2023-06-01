from Products.CMFCore.DirectoryView import registerDirectory
from zope.i18nmessageid import MessageFactory

AtlasMessageFactory = MessageFactory('agsci.atlas')

# Register indexers
from agsci.atlas import indexer

# Register skins directory
GLOBALS = globals()

registerDirectory('skins', GLOBALS)

def initialize(context):
    pass

# Returns an object with the keyword arguments as properties
def object_factory(**kwargs):

    # https://stackoverflow.com/questions/1305532/convert-python-dict-to-object
    class _(object):

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

            # Provide placeholder for empty text
            if not getattr(self, 'text', ''):
                self.text = 'N/A'

    return _(**kwargs)

# ZODB Update renames (for Plone 5 migration)
zodbupdate_renames = {
    'plone.app.event.dx.behaviors.FakeZone' : 'zope.interface.Interface',
}

from datetime import timedelta
from datetime import tzinfo

class FakeZone(tzinfo):
    """Fake timezone to be applied to EventBasic start and end dates before
    data_postprocessing event handler sets the correct one.
    """

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "FAKEZONE"

    def dst(self, dt):
        return timedelta(0)

from plone.app.event.dx import behaviors
behaviors.FakeZone = FakeZone
