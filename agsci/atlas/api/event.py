from agsci.api import BaseContainerView, BaseView

class EventView(BaseContainerView):

    def getData(self):
        data = super(EventView, self).getData()
        
        data['parent_id'] = self.context.getParentId()
        
        return data
