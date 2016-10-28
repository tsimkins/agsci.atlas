from plone.app.contenttypes.interfaces import INewsItem as _INewsItem
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider, implementer
from . import Container, IAtlasProduct

# News Item
@provider(IFormFieldProvider)
class INewsItem(_INewsItem, IAtlasProduct):

    pass

@implementer(INewsItem)
class NewsItem(Container):

    page_types = [u'Slideshow',]
