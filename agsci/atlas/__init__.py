from Products.CMFCore.DirectoryView import registerDirectory
from zope.i18nmessageid import MessageFactory

AtlasMessageFactory = MessageFactory('agsci.atlas')

# Register indexers
import indexer

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