from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IExtensionStructureMarker

from ..vocabulary.calculator import ExtensionMetadataCalculator

class IExtensionStructure(model.Schema):

    pass

class IStateExtensionTeam(IExtensionStructure):

    pass


@provider(IFormFieldProvider)
class IProgramTeam(IExtensionStructure):

    atlas_curriculum = schema.List(
        title=_(u"Curriculum(s)"),
        value_type=schema.TextLine(required=True),
        required=False,
    )

@implementer(IExtensionStructureMarker)
class ExtensionStructure(Container):

    def getQueryForType(self):

        content_type = self.Type()

        mc = ExtensionMetadataCalculator(content_type)

        metadata_value = mc.getMetadataForObject(self)

        return {content_type : metadata_value}


@adapter(IStateExtensionTeam)
class StateExtensionTeam(ExtensionStructure):

    pass

@adapter(IProgramTeam)
class ProgramTeam(ExtensionStructure):

    pass