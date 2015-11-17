from agsci.common.api import BaseContainerView, BaseView

class ArticleView(BaseContainerView):

    pass

class ArticlePageView(BaseView):

    def getData(self, recursive=True):
        data = self.getBaseData()
        data['text'] = self.context.text.raw
        return data
