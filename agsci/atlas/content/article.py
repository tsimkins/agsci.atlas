from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IArticleMarker
from . import IArticleDexterityContent
from plone.dexterity.content import Container

@provider(IFormFieldProvider)
class IArticle(IArticleDexterityContent):

    pass

class IArticlePage(IArticleDexterityContent):

    pass

@adapter(IArticle)
@implementer(IArticleMarker)
class Article(Container):
    page_types = [u'Video', u'Article Page', u'Slideshow',]
    
    def getPages(self):

        pages = self.listFolderContents({'Type' : self.page_types})
        
        return pages
