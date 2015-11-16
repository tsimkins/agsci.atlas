from agsci.common.api import BaseView
from agsci.common.utilities import getText

class ArticleView(BaseView):

    def getContents(self):
        return self.context.listFolderContents()

    def getData(self, recursive=True):
        data = self.getBaseData()

        if recursive:
            contents = self.getContents()
            
            if contents:
                data['contents'] = []
                
                for o in contents:
    
                    api_data = o.restrictedTraverse('@@api')
    
                    data['contents'].append(api_data.getFilteredData(recursive=False))

        return data

class ArticlePageView(BaseView):

    def getData(self, recursive=True):
        data = self.getBaseData()
        data['text'] = self.context.text.raw
        return data
