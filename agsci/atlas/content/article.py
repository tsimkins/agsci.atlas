from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IArticleMarker
from . import IArticleDexterityContent
from . import Container, IAtlasProduct

@provider(IFormFieldProvider)
class IArticle(IAtlasProduct, IArticleDexterityContent):

    pass

class IArticlePage(IArticleDexterityContent):

    pass

@adapter(IArticle)
@implementer(IArticleMarker)
class Article(Container):

    page_types = [u'Video', u'Article Page', u'Slideshow',]
    
