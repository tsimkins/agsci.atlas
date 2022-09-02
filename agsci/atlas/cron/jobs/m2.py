from Products.CMFPlone.utils import safe_unicode

from .magento import SetMagentoInfo as _SetMagentoInfo
from .magento import RepushStaleProducts as _RepushStaleProducts

from agsci.atlas.constants import M2_DATA_URL
from agsci.atlas.content.adapters import EventGroupCountyDataAdapter

class SetMagentoInfo(_SetMagentoInfo):

    title = "Set Magento SKU/URL (M2)"

    cache_key = 'M2_DATA'
    MAGENTO_DATA_URL = M2_DATA_URL

    # Hard Code enabled
    enabled = True

class RepushStaleProducts(_RepushStaleProducts):

    title = 'Re-push stale products (M2)'

    cache_key = 'M2_DATA'
    MAGENTO_DATA_URL = M2_DATA_URL

    # Hard Code enabled
    enabled = True

    limit = 25

    grace_period = 24 # One Day

    def updated_at(self, uid):
        return self.by_plone_id(uid).get('updated_at', '9999')

    def type_order(self, r):

        if r.review_state in ('expired',):
            return 50

        if r.Type in (
            'Conference Group',
            'Webinar Group',
            'Workshop Group',
        ):
            adapted = EventGroupCountyDataAdapter(r.getObject())

            if [x for x in adapted.upcoming_events]:
                return 0

        return {
            "App": 3,
            "Article": 3,
            "Conference Group": 2,
            "Cvent Event": 1,
            "External Event": 1,
            "Hyperlink": 5,
            "Learn Now Video": 4,
            "Learn Now Video Series": 4,
            "News Item": 3,
            "Online Course": 2,
            "Online Course Group": 2,
            "Person": 6,
            "Program": 6,
            "Publication": 3,
            "Smart Sheet": 4,
            "Webinar": 10,
            "Webinar Group": 2,
            "Workshop Group": 2
        }.get(r.Type, 9999)

    @property
    def products(self):

        # Get all active products in Magento
        results = self.portal_catalog.searchResults({
            'review_state' : ['published-inactive', 'published', 'expired'],
            'object_provides' : [
                'agsci.atlas.content.IAtlasProduct',
                'agsci.person.content.person.IPerson'
            ],
            'modified' : self.modified_crit,
            'UID' : self.plone_ids,
        })

        # Sort by updated date in Magento
        results = sorted(results, key=lambda x: self.updated_at(x.UID), reverse=False)
        results = sorted(results, key=lambda x: self.type_order(x), reverse=False)

        # Set counter
        counter = 0

        # Only grab limit products
        for r in results:

            # Skip expired child products
            if r.review_state in ['expired',] and r.IsChildProduct:
                continue

            if self.is_public_store(r):
                counter = counter + 1

                self.log("Product %s %s (Last updated %s) REIMPORTED: %r" % (
                        safe_unicode(r.Type),
                        safe_unicode(r.Title),
                        self.updated_at(r.UID),
                        (counter <= self.limit),
                    )
                )

                if counter <= self.limit:
                    yield r

        self.log("Queue: %d" % counter)