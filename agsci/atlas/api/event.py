from agsci.api.api import BaseContainerView

class EventView(BaseContainerView):

    def getData(self):
        data = super(EventView, self).getData()
        
        data['parent_id'] = self.context.getParentId()
        data['available_to_public'] = self.context.isAvailableToPublic()
        data['youth_event'] = self.context.isYouthEvent()
        return data

class EventContainerView(BaseContainerView):

    def getData(self):
        data = super(EventContainerView, self).getData()

        return data

    def getContents(self):
        return self.context.getContents(full_objects=True)
