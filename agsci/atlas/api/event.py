from agsci.api import BaseContainerView, BaseView

class EventView(BaseContainerView):

    def getData(self):
        data = super(EventView, self).getData()
        
        data['parent_id'] = self.context.getParentId()
        
        return data

class EventContainerView(BaseContainerView):

    def getData(self):
        data = super(EventContainerView, self).getData()

        return data

    def getContents(self):
        return self.context.getContents(full_objects=True)