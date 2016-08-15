from plone.autoform.interfaces import IFormFieldProvider
from zope.component import adapter
from zope.interface import provider
from . import Container, IAtlasProduct

@provider(IFormFieldProvider)
class IToolApplication(IAtlasProduct):

    pass

@adapter(IToolApplication)
class ToolApplication(Container):

    pass
