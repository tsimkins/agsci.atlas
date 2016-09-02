from datetime import timedelta
from plone.dexterity.content import Item
from urlparse import urlparse, parse_qs
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

@adapter(IArticleVideo)
@implementer(IVideoMarker)
class ArticleVideo(Item):

    def getVideoAspectRatio(self):
        return getattr(self, 'aspect_ratio', None)

    def getVideoAspectRatioDecimal(self):
        v = self.getVideoAspectRatio()

        try:
            if ':' in v:
                (w,h) = [float(x) for x in v.split(':')]
                return w/h
        except:
            return None

    def getVideoProvider(self):
        return getattr(self, 'provider', None)

    def getVideoChannel(self):
        return getattr(self, 'channel', None)

    def getVideoId(self):

        url = getattr(self, 'link', None)
        provider = self.getVideoProvider()

        if url and provider:

            url_object = urlparse(url)
            url_site = url_object.netloc

            # YouTube - grab the 'v' parameter

            if provider == 'youtube' or url_site.endswith('youtube.com'):

                params = parse_qs(url_object.query)

                v = params.get('v', None)

                if v:
                    if isinstance(v, list):
                        return v[0]
                    else:
                        return v

            # Vimeo - grab the first URl segent
            if provider == 'vimeo' or url_site.endswith('vimeo.com'):

                url_path = url_object.path

                return url_path.split('/')[1]

        return None

@adapter(IVideo)
@implementer(IVideoMarker)
class Video(ArticleVideo):

    def getTranscript(self):
        return getattr(self, 'transcript', None)

    def getDuration(self):
        return getattr(self, 'video_duration_milliseconds', None)

    def getDurationFormatted(self):
        v = self.getDuration()
        if v:
            return '%s' % timedelta(milliseconds=v)
