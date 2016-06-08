from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from agsci.atlas.interfaces import IExtensionStructureMarker
from plone.dexterity.content import Container
from plone.autoform.interfaces import IFormFieldProvider

class IExtensionStructure(model.Schema):

    pass

class IStateExtensionTeam(IExtensionStructure):

    pass


@provider(IFormFieldProvider)
class IProgramTeam(IExtensionStructure):

    curriculum = schema.List(
        title=_(u"Curriculum(s)"),
        value_type=schema.TextLine(required=True),
        required=False,
    )

@implementer(IExtensionStructureMarker)
class ExtensionStructure(Container):
    
    pass
    
@adapter(IStateExtensionTeam)
class StateExtensionTeam(ExtensionStructure):

    pass

@adapter(IProgramTeam)
class ProgramTeam(ExtensionStructure):

    pass