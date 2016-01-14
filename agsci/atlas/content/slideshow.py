from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import ISlideshowMarker
from article import IArticlePage

class ISlideshow(IArticlePage):

    pass

@adapter(ISlideshow)
@implementer(ISlideshowMarker)
class Slideshow(object):

    def __init__(self, context):
        self.context = context

    def getImages(self):
        return self.context.listFolderContents({'Type' : 'Image'})
