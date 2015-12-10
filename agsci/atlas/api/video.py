from article import ArticlePageView
from ..interfaces import IVideoMarker

class VideoView(ArticlePageView):

    def getData(self, recursive=True):
        # Get data from parent ArticlePageView, and add video-specific fields
        data = super(VideoView, self).getData(recursive=recursive)
        
        data['video_id'] = IVideoMarker(self.context).getVideoId()
        data['video_provider'] = IVideoMarker(self.context).getVideoProvider()
                
        return data



