from agsci.atlas import AtlasMessageFactory as _
from plone.app.contenttypes.interfaces import INewsItem as _INewsItem
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer

from ..interfaces import INewsContainerMarker, INewsItemMarker

# News Container (i.e. "Blog")

class INewsContainer(model.Schema):

    pass


@adapter(INewsContainer)
@implementer(INewsContainerMarker)
class NewsContainer(object):

    pass


# News Item

class INewsItem(_INewsItem):

    pass


@adapter(INewsItem)
@implementer(INewsContainerMarker)
class NewsItem(Container):

    pass
