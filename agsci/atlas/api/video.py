from article import ArticlePageView

class VideoView(ArticlePageView):

    def getData(self, recursive=True):
        # Get data from parent ArticlePageView, and add video-specific fields
        data = super(VideoView, self).getData(recursive=recursive)
        return data



