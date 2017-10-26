from . import NotificationConfiguration
from agsci.atlas.utilities import SitePeople
from Products.CMFPlone.utils import safe_unicode
from agsci.person.content.person import IPerson
from zope.component.interfaces import ObjectEvent

# Notification config object for scheduled notifications
class ScheduledNotificationConfiguration(NotificationConfiguration):

    def __init__(self, context=None, event=None):
        self.context = context
        self.event = ObjectEvent(self.context)

    def scrub(self, x):

        if x:
            return (u' '.join(safe_unicode(x).strip().split()))

        return ''

    @property
    def people_brains(self):
        sp = SitePeople()
        return sp.getPersonIdToBrain()

    def __call__(self):
        pass

class ProductOwnerStatusNotification(ScheduledNotificationConfiguration):

    # Hardcoded subject prefix
    SUBJECT_PREFIX = "Extension Product Status Report"

    # Review States
    review_states = [
        'requires_feedback',
        'expiring_soon',
        'private',
    ]

    # Exclude Types
    exclude_types = [
        'Curriculum',
        'Cvent Event',
        'Hyperlink',
        'Program',
        'Publicaton',
    ]

    @property
    def person_id(self):
        return self.context.getId()

    @property
    def owner_status_products(self):

        _id = self.person_id

        data = {}

        results = self.portal_catalog.searchResults(
            {
                'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                'sort_on' : 'sortable_title',
                'Owners' : [_id,],
                'review_state' : self.review_states
            }
        )

        for r in results:

            # If the product type should not be reported on, don't include.
            if r.Type in self.exclude_types:
                continue

            if not data.has_key(r.review_state):
                data[r.review_state] = []

            data[r.review_state].append(r)

        return data

    def generate_emails(self, data=[]):

        people_brains = self.people_brains

        _id = self.person_id

        if people_brains.has_key(_id):

            r = people_brains[_id]

            o = r.getObject()

            summary_report_blank = getattr(o, 'summary_report_blank', False)

            email_address = getattr(o, 'email', None)

            if email_address and email_address.endswith('@psu.edu'):

                text = [
                    u"This is a summary of products for which you are listed as an owner that require action.",
                ]

                def sort_key(x):
                    try:
                        return self.review_states.index(x)
                    except ValueError:
                        return 99999

                product_count = 0

                for review_state in sorted(data.keys(), key=lambda x: sort_key(x)):
                    review_state_title = review_state.replace(u'_', u' ').title()

                    text.append(u"")
                    text.append(review_state_title)
                    text.append(u"="*72)

                    for product in data[review_state]:

                        product_count = product_count + 1

                        text.extend([
                            u"",
                            u"    Title: %s" % self.scrub(product.Title),
                            u"    Description: %s" % self.scrub(product.Description),
                            u"    URL: %s" % product.getURL(),
                        ])

                        text.append(u"")
                        text.append(u"    " + u"-"*68)


                message = safe_unicode(u"\n".join(text)).encode('utf-8')

                if product_count or summary_report_blank:

                    yield {
                        'recipients' : email_address,
                        'subject' : u"%s (%d Products)" % (r.Title, product_count),
                        'message' : message,
                    }

    def __call__(self):

        if IPerson.providedBy(self.context):

            data = self.owner_status_products

            for kwargs in self.generate_emails(data):
                self.send_mail(**kwargs)
                yield kwargs.get('subject', '')
