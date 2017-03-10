from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from zope import schema
from zope.interface import provider
from . import Container, IAtlasProduct

@provider(IFormFieldProvider)
class IProgram(IAtlasProduct):

    __doc__ = 'Program Data'

    external_url = schema.TextLine(
        title=_(u"External URL"),
        description=_(u""),
        required=True,
    )


class Program(Container):

    pass

@provider(IFormFieldProvider)
class IProgramLink(IProgram):

    pass


class ProgramLink(Program):

    pass