from agsci.api import BaseContainerView, BaseView
from ..content.event import contact_fields, location_fields, registration_fields, IEvent, _IEvent, IEventContact

class EventView(BaseContainerView):

    structures = {
        'location' : location_fields,
        'contact' : contact_fields,
        'registration' : registration_fields,
    }

    def getData(self):
        data = super(EventView, self).getData()
        
        sd = self.getStructuredData(schemas=(IEvent, _IEvent, IEventContact), structures=self.structures)
        
        data.update(sd)

        return data
