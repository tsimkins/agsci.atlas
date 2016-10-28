from datetime import timedelta
from urlparse import urlparse, parse_qs
from zope.component import adapter
from zope.interface import implementer

from ..interfaces import IVideoMarker, IAtlasVideoFields

# Base class, so we always have a 'getData' method

class BaseAtlasAdapter(object):

    def getData(self):
        return {}

@adapter(IAtlasVideoFields)
@implementer(IVideoMarker)
class VideoDataAdapter(object):

    def __init__(self, context):
        self.context = context

    def getData(self):
        return {
            'video_aspect_ratio' : self.getVideoAspectRatio(),
            'video_aspect_ratio_decimal' : self.getVideoAspectRatioDecimal(),            
            'video_provider' : self.getVideoProvider(),  
            'video_id' : self.getVideoId(),
            'transcript' : self.getTranscript(),
            'video_duration_milliseconds' : self.getDuration(),
            'duration_formatted' : self.getDurationFormatted(),
        }

    def getVideoAspectRatio(self):
        return getattr(self.context, 'video_aspect_ratio', None)

    def getVideoAspectRatioDecimal(self):
        v = self.getVideoAspectRatio()

        try:
            if ':' in v:
                (w,h) = [float(x) for x in v.split(':')]
                return w/h
        except:
            return None

    def getVideoProvider(self):
        return getattr(self.context, 'video_provider', None)

    def getVideoId(self):

        url = getattr(self.context, 'video_link', None)
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

    def getVideoChannel(self):
        return getattr(self.context, 'video_channel_id', None)

    def getTranscript(self):
        return getattr(self.context, 'transcript', None)

    def getDuration(self):
        return getattr(self.context, 'video_duration_milliseconds', None)

    def getDurationFormatted(self):
        v = self.getDuration()
        if v:
            return '%s' % timedelta(milliseconds=v)