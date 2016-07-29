from plone.dexterity.content import Container
from plone.supermodel import model
from zope.component import adapter
from zope.interface import implementer
from agsci.atlas.interfaces import INewsContainerMarker

# News Container (i.e. "Blog")

class INewsContainer(model.Schema):

    pass


@adapter(INewsContainer)
@implementer(INewsContainerMarker)
class NewsContainer(Container):

    pass
