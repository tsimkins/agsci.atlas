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

    # Is the notification system in debug mode?
    @property
    def debug(self):
        return True

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
        'requires_initial_review',
        'expiring_soon',
        'private',
    ]

    @property
    def owner_status_products(self):

        _id = self.context.getId()

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

            if not data.has_key(_id):
                data[_id] = {}

            if not data[_id].has_key(r.review_state):
                data[_id][r.review_state] = []

            data[_id][r.review_state].append(r)

        return data

    def generate_emails(self, data=[], daily=True):

        email_data = []

        people_brains = self.people_brains

        for _id in data.keys():

            if people_brains.has_key(_id):

                r = people_brains[_id]

                o = r.getObject()

                email_address = getattr(o, 'email', None)

                if email_address and email_address.endswith('@psu.edu'):

                    text = [
                        u"This is a summary of products for which you are listed as an owner that require action.",
                    ]

                    products = data[_id]

                    def sort_key(x):
                        try:
                            return self.review_states.index(x)
                        except ValueError:
                            return 99999

                    for review_state in sorted(products.keys(), key=lambda x: sort_key(x)):
                        review_state_title = review_state.replace(u'_', u' ').title()

                        text.append(u"")
                        text.append(review_state_title)
                        text.append(u"="*72)

                        for product in products[review_state]:
                            text.extend([
                                u"",
                                u"    Title: %s" % self.scrub(product.Title),
                                u"    Description: %s" % self.scrub(product.Description),
                                u"    URL: %s" % product.getURL(),
                            ])

                            text.append(u"")
                            text.append(u"    " + u"-"*68)


                    message = safe_unicode(u"\n".join(text)).encode('utf-8')

                    email_data.append(
                        {
                            'recipients' : email_address,
                            'subject' : r.Title,
                            'message' : message,
                        }
                    )

        return email_data

    def __call__(self):

        if IPerson.providedBy(self.context):

            data = self.owner_status_products

            for kwargs in self.generate_emails(data):
                self.send_mail(**kwargs)
