from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.utils import safe_unicode
from DateTime import DateTime
from datetime import datetime
from plone.namedfile.file import NamedBlobFile
from time import sleep
from zope.globalrequest import getRequest

import os
import random
import re
import transaction

from agsci.person.events import setPersonLDAPInfo

from .. import CronJob
from agsci.atlas.browser.views import ExternalLinkCheckView
from agsci.atlas.constants import ACTIVE_REVIEW_STATES, CMS_DOMAIN, \
    EXTENSION_YOUTUBE_CHANNEL_ID, COLLEGE_YOUTUBE_CHANNEL_ID
from agsci.atlas.content.adapters import VideoDataAdapter
from agsci.atlas.content.behaviors import ILinkStatusReport
from agsci.atlas.content.event import IEvent
from agsci.atlas.events.location import onLocationProductCreateEdit
from agsci.atlas.indexer import ContentIssues, ContentErrorCodes, HasUpcomingEvents
from agsci.atlas.events.notifications.product_report import ArticleTextDump
from agsci.atlas.events.notifications.scheduled import ProductOwnerStatusNotification
from agsci.atlas.utilities import zope_root, localize

# For products whose expiration date has passed, flip them to the "Expired" status.
class ExpireExpiredProducts(CronJob):

    title = "Expire published/private products that have an expiration date in the past."

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'expires' : {
                'range' : 'max',
                'query' : self.now,
            },
            'review_state' : ['published', 'expiring_soon', 'private'],
        })

        msg = "Automatically expired based on expiration date."

        for r in results:
            o = r.getObject()

            try:
                self.portal_workflow.doActionFor(o, 'expired', comment=msg)
            except WorkflowException:
                self.log(u"Error expiring %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))
            else:
                o.setExpirationDate(None)
                o.reindexObject()

                self.log(u"Expired %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

# For Cvent Events that are updated to 'Cancelled', flip them to the "Expired" status.
class ExpireCancelledEvents(CronJob):

    title = "Expire Events that are updated to a 'Cancelled' status"

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.event.IEvent',
            'review_state' : ['published', 'expiring_soon'],
        })

        msg = "Automatically expired based on 'Cancelled' status"

        for r in results:
            o = r.getObject()

            if o.registration_status in [u'Cancelled']:

                self.portal_workflow.doActionFor(o, 'expired', comment=msg)
                o.setExpirationDate(None)
                o.reindexObject()

                self.log(u"Expired Cancelled %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

# For people whose expiration date has passed, flip them to the "Inactive" status.
class DeactivateExpiredPeople(CronJob):

    title = "Deactivate active people that have an expiration date in the past."

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.person.content.person.IPerson',
            'expires' : {
                'range' : 'max',
                'query' : self.now,
            },
            'review_state' : 'published',
        })

        msg = "Automatically deactivated based on expiration date."

        for r in results:
            o = r.getObject()

            self.portal_workflow.doActionFor(o, 'deactivate', comment=msg)
            o.reindexObject()

            self.log(u"Deactivated %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

# For products whose expiration date is coming in the next three months, flip
# them to the "Expiring Soon" status.
class SetExpiringSoonProducts(CronJob):

    future = 3*31 # 3 months

    title = "Set published products that will be expiring soon to the 'Expiring Soon' state."

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'expires' : {
                'range' : 'max',
                'query' : self.now + self.future,
            },
            'review_state' : ['published'],
            'Type' : [
                u'App',
                u'Article',
                u'Curriculum',
                u'Hyperlink',
                u'Learn Now Video',
                u'Online Course Group',
                u'Program',
                u'Publication',
                u'Smart Sheet',
                u'Webinar Group',
            ],
        })

        msg = "Set to 'Expiring Soon' based on pending expiration date."

        for r in results:
            o = r.getObject()

            # Skip events.  They do not need to be set to 'Expiring Soon'
            if IEvent.providedBy(o):
                continue

            self.portal_workflow.doActionFor(o, 'expiring_soon', comment=msg)
            o.reindexObject()

            self.log(u"Set %s '%s' (%s) to 'Expiring Soon'" % (r.Type, safe_unicode(r.Title), r.getURL()))

# Grab a random set of `sample_size` products and re-run the error check.
# Intended to be run frequently throughout the day.
class RerunErrorCheck(CronJob):

    title = "Rerun error check for published products."

    sample_size = 10

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ['published', 'expiring_soon'],
        })

        results = random.sample(results, self.sample_size)

        for r in results:
            o = r.getObject()

            current_issues = ContentIssues(o)
            current_errors = ContentErrorCodes(o)

            catalog_issues = r.ContentIssues
            catalog_errors = r.ContentErrorCodes

            self.log(u"Rechecking errors for %s '%s' (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

            if current_issues != catalog_issues or current_errors != catalog_errors:
                self.portal_catalog.catalog_object(o, idxs=['ContentErrorCodes', 'ContentIssues'])
                self.log(u"---> Reindexing %s '%s' (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

# Pull LDAP info for people in the "Active" status.
class UpdatePeopleLDAPInfo(CronJob):

    title = 'Pull LDAP info for people in the "Active" status.'

    sample_size = 10

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.person.content.person.IPerson',
            'review_state' : ['published',],
        })

        results = random.sample(results, self.sample_size)

        for r in results:
            o = r.getObject()

            updated = setPersonLDAPInfo(o, None)

            if updated:
                self.log(u"Updated %s '%s' (%s)" % (r.Type, safe_unicode(r.Title), r.getId))
            else:
                self.log(u"No update for %s '%s' (%s)" % (r.Type, safe_unicode(r.Title), r.getId))

class EmailActionReports(CronJob):

    summary_report_frequency = None
    sleep_interval = 1.0

    # Returns active people
    @property
    def people(self):

        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.person.content.person.IPerson',
            'review_state' : ['published',],
        })

    def run(self):

        for r in self.people:

            o = r.getObject()

            frequency = getattr(o, 'summary_report_frequency', None)

            if frequency and \
               frequency == self.summary_report_frequency:

                notify = ProductOwnerStatusNotification(o)

                for _ in notify():
                    self.log(u"Notified %s" % _)

                    # If we sent a notification, sleep so we don't send too many
                    # emails through at once.
                    sleep(self.sleep_interval)

class EmailActionReportsDaily(EmailActionReports):

    title = u"Email Action Reports (Daily)"
    summary_report_frequency = u"Daily"

class EmailActionReportsWeekly(EmailActionReports):

    title = u"Email Action Reports (Weekly)"
    summary_report_frequency = u"Weekly"

# Dump the text from publications to text files
class DumpPublicationText(CronJob):

    title = 'Dump Publication Article Text'

    prefix_re = re.compile("^(\d*[A-Z]+)", re.I|re.M)

    def prefix(self, sku):

        m = self.prefix_re.match(sku)

        if m:
            return m.group(0)

        return 'NO_PREFIX'

    def run(self):

        results = self.portal_catalog.searchResults(
            {
                'Type' : 'Article',
                'review_state' : 'published'
            }
        )

        for r in results:

            o = r.getObject()

            sku = getattr(o, 'publication_reference_number', None)

            if sku:

                v = ArticleTextDump(o)

                sku = v.scrub(sku).replace(' ', '_')

                try:
                    full_text = v()

                except:
                    self.log(u"Error %s (%s)" % (safe_unicode(r.Title), sku))

                else:

                    # Make a prefix directory
                    prefix = self.prefix(sku)

                    output_dir = "%s/publications/%s" % (zope_root, prefix)

                    try:
                        os.mkdir(output_dir)
                    except OSError:
                        pass

                    output = open("%s/%s.txt" % (output_dir, sku), "w")

                    output.write(full_text.encode('utf-8'))

                    output.close()

                    self.log(u"Dumped %s (%s)" % (safe_unicode(r.Title), sku))

class ExternalLinkCheck(CronJob):

    title = "Checks External Links In Products"
    limit = 10

    def run(self):

        # Get active products with links
        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ACTIVE_REVIEW_STATES,
            'ContentErrorCodes' : 'ExternalLinkCheck',
        })

        # Grab the least-recently updated `limit` number of products
        _ = []

        for r in results:

            o = r.getObject()

            if ILinkStatusReport.providedBy(o):

                link_report_date = getattr(o, 'link_report_date', None)

                if not link_report_date:
                    link_report_date = datetime.min

                _.append((link_report_date, o))

        _.sort()

        _ = _[:self.limit]

        _ = [x[1] for x in _]

        # Iterate through those and run the link_check() method of the
        # ExternalLinkCheckView, which writes a link report back to the object.
        for o in _:

            self.log(u"External Link Check For %s %s (%s)" % (o.Type(), safe_unicode(o.Title()), o.absolute_url()))

            v = ExternalLinkCheckView(o, getRequest())

            try:
                for error in v.link_check():
                    self.log(safe_unicode(repr(error)))
            except:
                self.log("Error checking links")

# Updates the HasUpcomingEvents index for Event Groups.
class UpdateEventGroupUpcomingEvents(CronJob):

    title = "Updates the HasUpcomingEvents index for Event Groups"

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
            'review_state' : ['published', ],
        })

        for r in results:
            o = r.getObject()

            _catalog = not not r.HasUpcomingEvents
            _actual = not not HasUpcomingEvents(o)()

            if _catalog != _actual:

                self.portal_catalog.catalog_object(o, update_metadata=1)

                self.log(u"Updated HasUpcomingEvents for %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

            else:
                self.log(u"OK: %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

# Update the physical address for people who are based in county offices
class UpdatePersonOfficeAddress(CronJob):

    title = "Update the physical address for people who are based in county offices"

    @property
    def county_info(self):

        data = {}

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.county.ICounty',
        })

        for r in results:
            o = r.getObject()
            v = o.restrictedTraverse('@@api')
            _data = v.getData()
            data[_data['county'][0]] = _data

        return data


    def compare(self, _1, _2):
        if isinstance(_1, (tuple, list)) and isinstance(_2, (tuple, list)):
            return tuple(_1) == tuple(_2)
        return _1 == _2

    def run(self):
        # Get the API data for the counties
        county_info = self.county_info

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.person.content.person.IPerson',
            'expires' : {
                'range' : 'min',
                'query' : self.now,
            },
            'County' : county_info.keys(),
            'review_state' : 'published',
        })

        for r in results:

            # Skip people with not exactly one county
            if len(r.County) != 1:
                continue

            # Updated items
            updated = []

            # Obtain info for person county
            county = r.County[0]
            _ = county_info[county]

            # County Location info
            _venue = _.get('venue', '')
            _street_address = _.get('address', [])
            _city = _.get('city', '')
            _state = _.get('state', '')
            _zip_code = _.get('zip', '')

            if _street_address:
                _street_address = list(_street_address)

            # Get the object and fields
            o = r.getObject()

            for (fname, value) in [
                ('venue', _venue),
                ('street_address', _street_address),
                ('city', _city),
                ('state', _state),
                ('zip_code', _zip_code),
            ]:

                v = getattr(o, fname, None)

                if not self.compare(v, value):
                    updated.append(fname)
                    setattr(o, fname, value)

            if updated:
                onLocationProductCreateEdit(o, None, force=True)
                o.reindexObject()

                self.log(u"Updated %s %s (%s) %r" % (r.Type, safe_unicode(r.Title), r.getURL(), updated))

class UpdateEventsNewsItem(CronJob):

    title = "Update the Excel file in the News Item that lists upcoming events."

    @property
    def news_item(self):
        results = self.portal_catalog.searchResults({
            'Type' : 'News Item',
            'getId' : 'download-events',
        })

        for r in results:
            return r.getObject()

    @property
    def field(self):
        v = self.context.restrictedTraverse('@@export_events')

        data = v.output_file

        if data:

            filename = u"%s-download-events.xls" % localize(datetime.now()).strftime('%Y%m%d')

            return NamedBlobFile(
                filename=filename,
                contentType=v.mime_type,
                data=data
            )

    def run(self):
        news_item = self.news_item

        if news_item:
            field = self.field

            if field:

                updated = localize(datetime.now())

                for o in news_item.listFolderContents({
                    'Type' : 'File',
                }):
                    o.file = field

                o.setEffectiveDate(updated)
                o.reindexObject()

                news_item.setEffectiveDate(updated)
                news_item.reindexObject()

                self.log(u"Updated %s file with %s" % (news_item.absolute_url(), field.filename))

            else:
                self.log(u"No data. Did not update %s file." % news_item.absolute_url())

        else:

            self.log(u"Could not find News Item")

# Download and set the YouTube transcript for Learn Now Videos
class SetLearnNowVideoTranscript(CronJob):

    months = 6

    title = "Download and set the YouTube transcript for Learn Now Videos"

    def run(self):

        results = self.portal_catalog.searchResults({
            'Type' : 'Learn Now Video',
            'sort_on' : 'effective',
            'sort_order' : 'reverse',
            'effective' : {
                'range' : 'min',
                'query' : DateTime() - (30.5*self.months)
            }
        })

        for r in results:
            o = r.getObject()

            adapted = VideoDataAdapter(o)
            video_id = adapted.getVideoId()
            video_channel = adapted.getVideoChannel()

            if video_channel not in (
                EXTENSION_YOUTUBE_CHANNEL_ID,
                COLLEGE_YOUTUBE_CHANNEL_ID
            ):
                self.log(u"Skipping %s [Not in College/Extension YouTube Channel]" % video_id)
                continue

            if not adapted.getTranscript():
                self.log(u"Checking for transcript for %s" % video_id)

                data = adapted.getYouTubeTranscript()

                if data:

                    self.log(u"Setting transcript for %s" % r.getURL())

                    adapted.setTranscript(data)
                    o.reindexObject()