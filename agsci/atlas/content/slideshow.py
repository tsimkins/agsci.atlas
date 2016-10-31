from zope.component import adapter
from zope.interface import implementer
from ..interfaces import ISlideshowMarker
from .article import IArticlePage
from plone.dexterity.content import Container

class ISlideshow(IArticlePage):

    pass


class Slideshow(Container):

    pass
