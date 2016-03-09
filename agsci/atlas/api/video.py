from article import ArticlePageView
from ..interfaces import IVideoMarker

class VideoView(ArticlePageView):

    def getData(self):
        # Get data from parent ArticlePageView, and add video-specific fields
        data = super(VideoView, self).getData()
        
        data['video_id'] = IVideoMarker(self.context).getVideoId()
        data['video_channel_id'] = IVideoMarker(self.context).getVideoChannel()
        data['video_provider'] = IVideoMarker(self.context).getVideoProvider()
        data['video_aspect_ratio'] = IVideoMarker(self.context).getVideoAspectRatio()
        data['video_aspect_ratio_decimal'] = IVideoMarker(self.context).getVideoAspectRatioDecimal()

        return data



class VideoFreeView(VideoView):

    def getData(self):
        # Get data from parent VideoView, and add video product-specific fields
        data = super(VideoFreeView, self).getData()
        
        data['video_duration_milliseconds'] = self.context.getDuration()
        data['duration_formatted'] = self.context.getDurationFormatted()
        data['transcript'] = self.context.getTranscript()
                        
        return data