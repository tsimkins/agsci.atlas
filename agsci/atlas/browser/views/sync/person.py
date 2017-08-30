from DateTime import DateTime
from plone.namedfile.file import NamedBlobImage
from zope.component.hooks import getSite

import json
import urllib2

from agsci.atlas.utilities import SitePeople
from agsci.person.content.vocabulary import ClassificationsVocabulary

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
        default_url = 'http://archive.extension.psu.edu/directory'

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

        # Get listing of valid classifications from current directory
        valid_classifications = [x.value for x in ClassificationsVocabulary()(self.context)]

        # Add other classifications that are OK to import
        valid_classifications.extend([
            'Adjunct and Affiliate Faculty',
            'Emeritus and Retired Faculty',
            'Emeritus Professors and Retirees',
            'Adjunct & Retired Faculty',
            'Emeritus Faculty',
            'Emeriti and Retired',
            'Assistant to the Director',
            'Retired and Emeritus Faculty',
            'District Directors',
        ])

        # Iterate through contents
        for i in people:

            # Increment counter
            counter = counter + 1

            # Set 'product_type' as 'type'
            i['product_type'] = i.get('type', None)

            # If we were passed a URL, don't do a classification check
            if self.person_url:
                pass

            # If the person is not an employee with a valid classification, skip
            # this record.
            elif not set(i.get('directory_classifications', [])) & set(valid_classifications):

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

            # Finalize item
            self.finalize(item)

            # Append the data structure converted from the JSON data to rv
            rv.append(json.loads(self.getJSON(item)))

            # Log progress
            self.log("Done with %s, %d/%d" % (v.data.get_id, counter, total_people))

        # Deactivate people who are expired and active
        self.deactivateExpiredPeople()

        # Return a full JSON dump of the updated data
        return json.dumps(rv, indent=4, sort_keys=True)

    # Deactivate people who are expired and active.
    def deactivateExpiredPeople(self):

        sp = SitePeople()

        expired_active_people = sp.expired_active_people

        for r in expired_active_people:

            o = r.getObject()

            msg = 'Automatically deactivating %s (%s) based on expiration date.' % (r.Title, r.getId)

            self.log(msg)
            sp.wftool.doActionFor(o, 'deactivate', comment=msg)
            o.reindexObject()

        self.log("Deactivated %d people" % len(expired_active_people))