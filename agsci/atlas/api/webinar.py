from agsci.api import BaseView
from agsci.api.api.plone_types.file import FileView

class WebinarView(BaseView):

    def getData(self):
        data = super(WebinarView, self).getData()

        data['parent_id'] = self.context.getParentId()
        data['available_to_public'] = self.context.isAvailableToPublic()

        # Get the webinar recording object, and attach its field as an item
        pages = self.context.getPages()

        if pages:
            webinar_recording = pages[0]
            link = getattr(webinar_recording, 'webinar_recorded_url', None)

            if link:
                data['webinar_recorded_url'] = link
                
                # Add additional fields to the parent webinar.
                for k in ['duration_formatted', 'transcript']:
                    v = getattr(webinar_recording, k, None)
                    
                    if v:
                        data[k] = v 

                # Now, attach the handouts and presentations
                files = webinar_recording.getPages()

                if files:
                    data['webinar_recorded_files'] = []

                    for i in files:
                        file_api_view = i.restrictedTraverse('@@api')
                        data['webinar_recorded_files'].append(file_api_view.getData())

        return data

class WebinarFileView(FileView):

    def getData(self):
        data = super(WebinarFileView, self).getData()

        # Remove fields that are acquired from parent webinar
        for i in ['event_start_date', 'event_end_date', 'description']:
            if data.has_key(i):
                del data[i]

        return data
