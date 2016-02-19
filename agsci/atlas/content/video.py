from agsci.atlas import AtlasMessageFactory as _
from article import IArticlePage
from plone.supermodel import model
from urlparse import urlparse, parse_qs
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from ..interfaces import IVideoMarker
from plone.dexterity.content import Item
from datetime import timedelta

video_providers = SimpleVocabulary(
    [SimpleTerm(value=x.lower(), title=_(x)) for x in (u'YouTube', u'Vimeo')]
)

video_aspect_ratio = SimpleVocabulary(
    [SimpleTerm(value=x, title=_(x)) for x in (u'16:9', u'3:2', u'4:3') ]
)

class IVideo(IArticlePage):

    link = schema.TextLine(
        title=_(u"Video Link"),
        required=True,
    )
    
    provider = schema.Choice(
        title=_(u"Video Provider"),
        vocabulary=video_providers,
        required=True,
    )

    aspect_ratio = schema.Choice(
        title=_(u"Video Aspect Ratio"),
        vocabulary=video_aspect_ratio,
        required=True,
    )
    
    channel = schema.TextLine(
        title=_(u"Video Channel"),
        required=False,
    )

class IVideoFree(IVideo):

    transcript = schema.Text(
        title=_(u"Transcript"),
        required=False,
    )
    
    video_duration_milliseconds = schema.Int(
        title=_(u"Video Length (In Milliseconds)"),
        required=False,
    )


class IVideoPaid(IVideoFree):

    pass

@adapter(IVideo)
@implementer(IVideoMarker)
class Video(Item):

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

@adapter(IVideoFree)
@implementer(IVideoMarker)
class VideoFree(Video):

    def getTranscript(self):
        return getattr(self, 'transcript', None)

    def getDuration(self):
        return getattr(self, 'video_duration_milliseconds', None)
        
    def getDurationFormatted(self):
        v = self.getDuration()
        if v:
            return '%s' % timedelta(milliseconds=v)