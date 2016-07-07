from article import ArticleView
from agsci.api import BaseContainerView, BaseView
from ..interfaces import INewsItemMarker

class NewsItemView(ArticleView):

    def getPageCount(self):
        pages = INewsItemMarker(self.context).getPages()

        # Adding +1 to page_count, since the news item body text is implicitly a page
        return len(pages) + 1
        
class ArticlePageView(BaseView):

    pass
