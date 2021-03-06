from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import provider

from agsci.atlas import AtlasMessageFactory as _

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


class ExtensionStructure(Container):

    def getQueryForType(self):

        content_type = self.Type()

        mc = ExtensionMetadataCalculator(content_type)

        metadata_value = mc.getMetadataForObject(self)

        return {content_type : metadata_value}


class StateExtensionTeam(ExtensionStructure):

    pass


class ProgramTeam(ExtensionStructure):

    pass