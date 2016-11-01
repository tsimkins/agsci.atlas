from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider
from . import Container, IAtlasProduct

@provider(IFormFieldProvider)
class IToolApplication(IAtlasProduct):

    pass


class ToolApplication(Container):

    pass


# Smartsheet
class ISmartSheet(IToolApplication):
    pass

class SmartSheet(ToolApplication):
    pass


# Application
class IApp(IToolApplication):
    pass

class App(ToolApplication):
    pass