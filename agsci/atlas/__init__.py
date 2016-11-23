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
