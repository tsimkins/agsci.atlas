from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IArticleMarker
from . import IArticleDexterityContent

@provider(IFormFieldProvider)
class IArticle(IArticleDexterityContent):

    pass

class IArticlePage(IArticleDexterityContent):

    pass

@adapter(IArticle)
@implementer(IArticleMarker)
class Article(object):

    def __init__(self, context):
        self.context = context
    
    def getPages(self):

        page_types = [u'Video', u'Article Page', u'Slideshow',]

        pages = self.context.listFolderContents({'Type' : page_types})
        
        return pages
