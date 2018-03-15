from Products.CMFPlone.utils import safe_unicode
from time import sleep

import os
import random
import re

from agsci.person.events import setPersonLDAPInfo

from .. import CronJob
from agsci.atlas.content.event import IEvent
from agsci.atlas.indexer import ContentIssues, ContentErrorCodes
from agsci.atlas.events.notifications.product_report import ArticleTextDump
from agsci.atlas.events.notifications.scheduled import ProductOwnerStatusNotification
from agsci.atlas.utilities import zope_root

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

            self.portal_workflow.doActionFor(o, 'expired', comment=msg)
            o.setExpirationDate(None)
            o.reindexObject()

            self.log(u"Expired %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

# For Cvent Events that are updated to 'Cancelled', flip them to the "Expired" status.
class ExpireCancelledCventEvents(CronJob):

    title = "Expire Cvent Events that are updated to a 'Cancelled' status"

    def run(self):

        results = self.portal_catalog.searchResults({
            'Type' : 'Cvent Event',
            'review_state' : ['published', 'expiring_soon'],
        })

        msg = "Automatically expired based on 'Cancelled' status"

        for r in results:
            o = r.getObject()

            if o.registration_status in [u'Cancelled']:

                self.portal_workflow.doActionFor(o, 'expired', comment=msg)
                o.setExpirationDate(None)
                o.reindexObject()

                self.log(u"Expired Cancelled Cvent Event %s %s (%s)" % (r.Type, safe_unicode(r.Title), r.getURL()))

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
                u'Conference Group',
                u'Curriculum',
                u'Hyperlink',
                u'Learn Now Video',
                u'Online Course Group',
                u'Program',
                u'Publication',
                u'Smart Sheet',
                u'Webinar Group',
                u'Workshop Group'
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

# Since Event Groups have counties listed, these will only be updated when the Event Group is imported.
class TouchEventGroups(CronJob):

    title = 'Touch Event Groups'

    sample_size = 10

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
            'review_state' : ['published', 'expiring_soon'],
        })

        results = random.sample(results, self.sample_size)

        for r in results:
            o = r.getObject()

            if o.objectIds():
                self.log(u"Updated %s '%s' (%s)" % (r.Type, safe_unicode(r.Title), r.getId))
                o.reindexObject()

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