from article import ArticleView
from agsci.api import BaseContainerView, BaseView
from ..interfaces import INewsItemMarker

class NewsItemView(ArticleView):

    def getPageCount(self):
        pages = INewsItemMarker(self.context).getPages()
        return len(pages)
        
class ArticlePageView(BaseView):

    pass
