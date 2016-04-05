from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import INewsItemMarker
from plone.app.contenttypes.interfaces import INewsItem as _INewsItem
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer

# News Item

class INewsItem(_INewsItem):

    pass


@adapter(INewsItem)
@implementer(INewsItemMarker)
class NewsItem(Container):

    pass