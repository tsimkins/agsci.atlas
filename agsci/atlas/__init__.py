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
'agsci.atlas.content.structure.extension ProgramTeam' : 'persistent Persistent',
'agsci.atlas.content.structure.extension StateExtensionTeam' : 'persistent Persistent',
'App.Product ProductFolder' : 'persistent Persistent',
'plone.app.folder.nogopip GopipIndex' : 'persistent Persistent',
'Products.Archetypes.ArchetypeTool ArchetypeTool' : 'persistent Persistent',
'Products.Archetypes.ReferenceEngine ReferenceBaseCatalog' : 'persistent Persistent',
'Products.Archetypes.ReferenceEngine ReferenceCatalog' : 'persistent Persistent',
'Products.Archetypes.UIDCatalog UIDBaseCatalog' : 'persistent Persistent',
'Products.Archetypes.UIDCatalog UIDCatalog' : 'persistent Persistent',
'Products.ATContentTypes.tool.atct ATCTTool' : 'persistent Persistent',
'Products.ATContentTypes.tool.topic TopicIndex' : 'persistent Persistent',
'Products.CMFActionIcons.ActionIconsTool ActionIcon' : 'persistent Persistent',
'Products.CMFDefault.MetadataTool ElementSpec' : 'persistent Persistent',
'Products.CMFDefault.MetadataTool MetadataElementPolicy' : 'persistent Persistent',
'Products.CMFDefault.MetadataTool MetadataSchema' : 'persistent Persistent',
'Products.CMFPlone.ActionIconsTool ActionIconsTool' : 'persistent Persistent',
'Products.CMFPlone.CalendarTool CalendarTool' : 'persistent Persistent',
'Products.CMFPlone.DiscussionTool DiscussionTool' : 'persistent Persistent',
'Products.CMFPlone.FactoryTool FactoryTool' : 'persistent Persistent',
'Products.CMFPlone.InterfaceTool InterfaceTool' : 'persistent Persistent',
'Products.CMFPlone.MetadataTool MetadataTool' : 'persistent Persistent',
'Products.CMFPlone.UndoTool UndoTool' : 'persistent Persistent',
'Products.PasswordResetTool.PasswordResetTool PasswordResetTool' : 'persistent Persistent',
'Products.TinyMCE.utility TinyMCE' : 'persistent Persistent',

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
