from plone.dexterity.content import Item
from zope import schema

from agsci.atlas import AtlasMessageFactory as _
from ..interfaces import IVideoMarker
from . import IArticleDexterityContainedContent, IAtlasProduct
from .behaviors import IVideoBase

class IArticleVideo(IVideoBase, IArticleDexterityContainedContent):

    pass

class IVideo(IVideoBase, IAtlasProduct):

    __doc__ = "Video (Product)"

    transcript = schema.Text(
        title=_(u"Transcript"),
        required=False,
    )

    video_duration_milliseconds = schema.Int(
        title=_(u"Video Length (In Milliseconds)"),
        required=False,
    )


class BaseVideo(Item):

    pass

class ArticleVideo(BaseVideo):

    pass

class Video(ArticleVideo):

    pass