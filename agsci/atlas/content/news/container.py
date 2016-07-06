from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from agsci.atlas.interfaces import INewsContainerMarker

# News Container (i.e. "Blog")

class INewsContainer(model.Schema):

    pass


@adapter(INewsContainer)
@implementer(INewsContainerMarker)
class NewsContainer(Container):

    pass
