from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import ISlideshowMarker
from .article import IArticlePage
from plone.dexterity.content import Container

class ISlideshow(IArticlePage):

    pass

@adapter(ISlideshow)
@implementer(ISlideshowMarker)
class Slideshow(Container):

    def getImages(self):
        return self.listFolderContents({'Type' : 'Image'})
