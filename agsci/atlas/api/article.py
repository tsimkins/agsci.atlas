from agsci.api import BaseContainerView, BaseView
from ..interfaces import IArticleMarker

class ArticleView(BaseContainerView):

    def getData(self):
        data = super(ArticleView, self).getData()
        
        page_count = self.getPageCount()
        data['page_count'] = page_count
        data['multi_page'] = ( page_count > 1 )

        return data

    def getPageCount(self):
        pages = IArticleMarker(self.context).getPages()
        return len(pages)
        
class ArticlePageView(BaseView):

    pass
