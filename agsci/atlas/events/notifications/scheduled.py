from . import NotificationConfiguration
from agsci.atlas.utilities import SitePeople
from Products.CMFPlone.utils import safe_unicode
from agsci.person.content.person import IPerson
from zope.component.interfaces import ObjectEvent

import textwrap

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

    # Help Text
    help_text = {
        'requires_feedback' : """
            These items require feedback before they can be published.
            Please check the 'History' link or your previous emails for
            more information.
        """,
        'private' : """
            These products are currently being edited in the Plone CMS. Please
            complete an updates, save the product, then select "Submit
            for publication" from the State dropdown to publish on the
            website.
            __BREAK__
            If you no longer want the product to be live on the website,
            you can select "Expire" from the State dropdown. Expired
            products will still be available in the Plone CMS for reference and
            can be restored at any time.
        """,
        'expiring_soon' : """
            This is a summary of articles, news, learn now videos, webinar
            recordings, smart sheets, and apps for which you are listed as 
            an owner and require action in the Plone CMS. You will receive
            separate communication regarding other product types, such as
            publications and online courses, that are managed in
            collaboration with the Marketing or Digital Ed teams. If no
            action is taken, the product will no longer show up on the
            public Extension site after the "Expires" date. However, expired
            products will still be available in the Plone CMS for reference 
            and can be restored at any time.
            __BREAK__
            Prior to the "Expires" date, please review the content of the
            product in the Plone CMS and take one of these three actions:
            __BREAK__
            * Retain with updates: Edit the product in the Plone CMS to make the
            necessary updates; Select "Submit for publication" from the
            State dropdown.
            __BREAK__
            * Retain, but no updates needed: If no updates are necessary
            and you would like to keep your product as-is, select "Submit
            for publication" from the State dropdown.
            __BREAK__
            * Expire, no longer relevant or needed: You may manually expire
             the product sooner in the Plone CMS by selecting "Expire" from the
             State dropdown.
        """,
    }

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

                    _help_text = self.help_text.get(review_state, None)

                    if _help_text:
                        # Format and wrap
                        _help_text = " ".join(_help_text.strip().split())

                        _help_text = [x.strip() for x in _help_text.split('__BREAK__')]

                        _help_text = "\n\n".join(["\n".join(textwrap.wrap(x)) for x in _help_text])
                        text.append(_help_text.strip())

                    for product in data[review_state]:

                        product_count = product_count + 1

                        _text = [
                            u"",
                            u"    Product Type: %s" % self.scrub(product.Type),
                            u"    Title: %s" % self.scrub(product.Title),
                            u"    Description: %s" % self.scrub(product.Description),
                            u"    URL: %s" % product.getURL(),
                        ]

                        if review_state in ('expiring_soon',):
                            _text.append(
                                u"    Expires: %s" % product.expires.strftime('%Y-%m-%d'),
                            )

                        text.extend(_text)

                        text.append(u"")
                        text.append(u"    " + u"-"*68)

                text.append("\nPlease do not reply to this email; it is not a valid address. For questions or assistance, contact the web team by submitting an 'AgSci Website Support' request in Workfront: https://agsci.psu.edu/workfront-request\n")

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