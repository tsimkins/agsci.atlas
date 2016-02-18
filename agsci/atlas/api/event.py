from agsci.api import BaseContainerView, BaseView
from ..content.event import contact_fields, location_fields, registration_fields, IEvent, _IEvent, IEventContact

class EventView(BaseContainerView):

    def getData(self):
        data = super(EventView, self).getData()
        
        sd = self.getSchemaData(schemas=(IEvent, _IEvent, IEventContact),)
        
        data.update(sd)

        return data
