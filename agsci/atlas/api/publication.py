from agsci.api import BaseView

class PublicationView(BaseView):

    def getData(self):
        data = super(PublicationView, self).getData()
        
        page_count = self.context.getPageCount()
        
        if page_count:
            data['pages_count'] = page_count

        return data