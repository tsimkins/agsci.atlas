from DateTime import DateTime
from agsci.atlas.content.sync.mapping import mapCategories as _mapCategories
from agsci.person.events import onPersonEdit
from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedBlobImage
from zope.component.hooks import getSite
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import json
import transaction
import urllib2

from . import SyncContentView

class SyncPersonView(SyncContentView):

    # Translation of old to new attribute names
    translation = [
        ('last_name', 'last_name'),
        ('first_name', 'first_name'),
        ('middle_name', 'middle_name'),
        ('suffix', 'suffix'),
        ('office_address', 'street_address'),
        ('office_state', 'state'),
        ('office_phone', 'phone_number'),
        ('office_city', 'city'),
        ('zip_code', 'zip_code'),
        ('email', 'email'),
        ('expires', 'expires'),
        ('directory_classifications', 'classifications'),
        ('counties', 'county'),
        ('job_titles', 'job_titles'),
        ('education', 'education'),
        ('extension_areas', 'areas_expertise'),
        ('fax_number', 'fax_number'),
        ('twitter_url', 'twitter_url'),
        ('facebook_url', 'facebook_url'),
        ('linkedin_url', 'linkedin_url'),
        ('username', 'get_id'),
    ]

    @property
    def import_path(self):
        return getSite()['directory']

    def requestValidation(self):
        return True

    def getRequestDataAsArguments(self, v):
        data = super(SyncPersonView, self).getRequestDataAsArguments(v)

        # Get old and new fields from translation, and add values for new fields
        # if they exist
        for (old_key, new_key) in self.translation:

            value = getattr(v.data, old_key)

            if value:
                data[new_key] = value

        # Map categories from old to new
        categories = self.mapCategories(v.data.extension_topics, v.data.extension_subtopics)

        if categories:
            for (_k, _v) in categories.iteritems():
                if _v:
                    data[_k] = _v

        return data

    def getId(self, v):
        return v.data.get_id

    def importContent(self):

        # Initialize the return value list
        rv = []

        # This is the URL of the current directory
        url = 'http://extension.psu.edu/directory/@@api-json?full=True'

        # Get JSON data from request
        data = urllib2.urlopen(url).read()

        # Load JSON data into structure
        json_data = json.loads(data)

        # Extract only the people from the contents
        people = [x for x in json_data['contents'] if x.get('type', '') == 'Person']

        # Count total people, and initialize counter
        total_people = len(people)
        counter = 0

        # Log progress
        self.log("Downloaded data, %d entries" % total_people)

        # Iterate through contents
        for i in people:

            # Increment counter
            counter = counter + 1

            # Set 'product_type' as 'type'
            i['product_type'] = i.get('type', None)

            # Set categories for mapping

            # If the person is not an employee, skip this record
            if not (set(i.get('directory_classifications', [])) & \
                    set(['Staff', 'Faculty', 'Educators'])):

                continue

            # Create content importer from person JSON data
            v = self.content_importer(i)

            # Check for person existing in directory (import_path) and create or
            # update appropriately
            if v.data.get_id in self.import_path.objectIds():

                # Update
                item = self.import_path[v.data.get_id]

                # Only update if feed last updated date is greater than the item
                # last updated date
                if DateTime(v.data.modified) > item.modified():
                    item = self.updateObject(item, v)
                    notify(ObjectModifiedEvent(item))

                    # Log progress
                    self.log("Updated %s" % v.data.get_id)
                else:
                    # Log progress
                    self.log("Skipped %s" % v.data.get_id)
                    continue

            else:
                # Create
                item = self.createObject(self.import_path, v)
                notify(ObjectModifiedEvent(item))

                # Log progress
                self.log("Created %s" % v.data.get_id)

            # Set Image
            image_url = i.get('image_url', None)

            if image_url:
                img = NamedBlobImage()
                img.data = urllib2.urlopen(image_url).read()
                item.leadimage = img

            # Set text field for bio. Note this is not a RichTextValue, since
            # it's a field inherited from another schema
            if v.data.html:
                item.bio = v.data.html

            # Run the post-edit event
            onPersonEdit(item, None)

            # Reindex object
            item.reindexObject()

            # Append the data structure converted from the JSON data to rv
            rv.append(json.loads(self.getJSON(item)))

            # Commit changes
            transaction.commit()

            # Log progress
            self.log("Done with %s, %d/%d" % (v.data.get_id, counter, total_people))

        # Return a full JSON dump of the updated data
        return json.dumps(rv,indent=4, sort_keys=True)