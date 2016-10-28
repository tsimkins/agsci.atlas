from plone.dexterity.content import Item
from zope import schema
from zope.component import adapter
from zope.interface import implementer

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

    def getVideoAspectRatio(self):
        return IVideoMarker(self).getVideoAspectRatio()

    def getVideoAspectRatioDecimal(self):
        return IVideoMarker(self).getVideoAspectRatioDecimal()

    def getVideoProvider(self):
        return IVideoMarker(self).getVideoProvider()

    def getVideoId(self):
        return IVideoMarker(self).getVideoId()

    def getVideoChannel(self):
        return IVideoMarker(self).getVideoChannel()

    def getTranscript(self):
        return IVideoMarker(self).getTranscript()

    def getDuration(self):
        return IVideoMarker(self).getDuration()

    def getDurationFormatted(self):
        return IVideoMarker(self).getDurationFormatted()


class ArticleVideo(BaseVideo):

    pass

class Video(ArticleVideo):

    pass