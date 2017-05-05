from DateTime import DateTime
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
        ('directory_classifications', 'classifications'),
        ('counties', 'county'),
        ('job_titles', 'job_titles'),
        ('education', 'education'),
        ('extension_areas', 'areas_expertise'),
        ('fax_number', 'fax_number'),
        ('twitter_url', 'twitter_url'),
        ('facebook_url', 'facebook_url'),
        ('linkedin_url', 'linkedin_url'),
        ('get_id', 'username'),
    ]

    @property
    def import_path(self):
        return getSite()['directory']

    def requestValidation(self):
        return True

    def getRequestDataAsArguments(self, v, item=None):
        data = super(SyncPersonView, self).getRequestDataAsArguments(v, item=None)

        # Get old and new fields from translation, and add values for new fields
        # if they exist
        for (old_key, new_key) in self.translation:

            value = getattr(v.data, old_key)

            # Handle street address data type change.
            if new_key in ['street_address',]:
                if isinstance(value, (str, unicode)):
                    value = value.strip()
                    value = value.replace('\r', '\n')
                    value = value.split('\n')
                    value = [x.strip() for x in value if x.strip()]

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

    @property
    def person_url(self):
        return self.request.get('url', None)

    def getPeople(self):

        def isPerson(x):
            return x.get('type', '') == 'Person'

        # This is the URL of the Extension directory
        default_url = 'http://extension.psu.edu/directory'

        # If we were passed a URL, just do one person
        url = self.person_url

        if url:

            if url.endswith('/'):
                url = url[:-1]

        else:

            url = default_url


        url = '%s/@@api-json?full=True' % url

        # Get JSON data from request
        data = urllib2.urlopen(url).read()

        # Load JSON data into structure
        json_data = json.loads(data)

        # If this is a multi-person list, extract only the people from the
        # 'contents' and return
        if json_data.has_key('contents'):
            return filter(isPerson, json_data['contents'])
        elif isPerson(json_data):
            return [json_data,]
        else:
            return []

    def importContent(self):

        # Grab the "force" parameter from the URL, and convert to boolean.
        # If this is true, everyone will be updated.
        force_update = not not self.request.get('force', False)

        # Initialize the return value list
        rv = []

        # Get a list of the people
        people = self.getPeople()

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

            # If we were passed a URL, don't do a classification check
            if self.person_url:
                pass

            # If the person is not an employee, skip this record
            elif not (set(i.get('directory_classifications', [])) & \
                    set(['Assistant Director of Programs',
                         'Assistant to the Director', 'Associate Director',
                         'Director', 'District Directors', 'Educators',
                         'Retired and Emeritus Faculty',
                         'Emeritus and Retired Faculty',
                         'Adjunct & Retired Faculty',
                         'Adjunct and Affiliate Faculty',
                         'Emeriti and Retired',
                         'Emeritus Faculty',
                         'Emeritus Professors and Retirees',
                         'Faculty', 'Staff',])):

                continue

            # Create content importer from person JSON data
            v = self.content_importer(i)

            # Check for person existing in directory (import_path) and create or
            # update appropriately
            if v.data.get_id in self.import_path.objectIds():

                # Update
                item = self.import_path[v.data.get_id]

                # Only update if feed last updated date is greater than the item
                # last updated date.  If a "force" parameter is provided in the
                # URL, all objects will be updated.
                if force_update or DateTime(v.data.modified) > item.modified():
                    item = self.updateObject(item, v)

                    # Log progress
                    self.log("Updated %s" % v.data.get_id)
                else:
                    # Log progress
                    self.log("Skipped %s" % v.data.get_id)
                    continue

            else:
                # Create
                item = self.createObject(self.import_path, v)

                # Log progress
                self.log("Created %s" % v.data.get_id)

            # Set expiration date
            if v.data.expires:
                expires = DateTime(v.data.expires)
                item.setExpirationDate(expires)

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

            # Reindex object
            item.reindexObject()

            # Commit changes
            transaction.commit()

            # Run the post-edit event
            notify(ObjectModifiedEvent(item))

            # Commit changes
            transaction.commit()

            # Append the data structure converted from the JSON data to rv
            rv.append(json.loads(self.getJSON(item)))

            # Log progress
            self.log("Done with %s, %d/%d" % (v.data.get_id, counter, total_people))

        # Return a full JSON dump of the updated data
        return json.dumps(rv,indent=4, sort_keys=True)