from Acquisition import aq_base
from DateTime import DateTime
from Products.CMFPlone.utils import safe_unicode
from datetime import timedelta
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest

import Missing
import requests

from agsci.atlas.constants import CMS_DOMAIN, DEFAULT_TIMEZONE
from agsci.atlas.content.adapters import EventGroupCountyDataAdapter
from .. import CronJob

MAGENTO_DATA_URL = "http://%s/magento.json" % CMS_DOMAIN

class MagentoJob(CronJob):

    cache_key = 'MAGENTO_DATA'

    keys = [
        'plone_id',
        'magneto_url',
        'sku',
    ]

    @property
    def enabled(self):

        try:
            return not not self.registry['agsci.atlas.magento_integration_enable']
        except:
            return False

    grace_period = 24 # 24 Hours grace period so we aren't reindexing constantly

    @property
    def request(self):
        return getRequest()

    @property
    def modified_crit(self):
        now = DateTime() - (self.grace_period/24.0)

        return {
            'query' : now,
            'range' : 'max',
        }

    # Job Title
    title = "Base Magento Job"

    def __init__(self, context):
        super(MagentoJob, self).__init__(context)

        # Set Magento data into a variable so we're not grabbing it every time
        self.data = self.compiled_data

    @property
    def compiled_data(self):

        cache = IAnnotations(self.request)
        key = self.cache_key

        if not cache.has_key(key):

            _ = {}

            for i in self._data:
                if not i.get('product_status', None) == u'Approved':
                    continue
                for k in self.keys:
                    if not _.has_key(k):
                        _[k] = {}
                    v = i.get(k, None)
                    if v:
                        _[k][v] = i

            cache[key] = _

        return cache[key]

    # Downloads the JSON data by SKU (uncached)
    @property
    def _data(self):

        try:
            response = requests.get(MAGENTO_DATA_URL)
            return response.json()

        except:
            return []

    def by_attr(self, attr, v):
        return self.data.get(attr, {}).get(v, {})

    def get_attrs(self, attr):
        v = self.data.get(attr, {}).keys()
        return [x for x in v if v]

    def by_plone_id(self, v):
        return self.by_attr('plone_id', v)

    def by_sku(self, v):
        return self.by_attr('sku', v)

    def by_magento_url(self, v):
        return self.by_attr('magento_url', v)

    @property
    def plone_ids(self):
        return self.get_attrs('plone_id')

    @property
    def skus(self):
        return self.get_attrs('sku')

    @property
    def magento_urls(self):
        return self.get_attrs('magento_url')

    # Only push stuff in the public store
    def is_public_store(self, r):

        o = r.getObject()

        store_view_id = getattr(o, 'store_view_id', [])

        if not store_view_id:
            store_view_id = []

        return 2 in store_view_id

    def run(self):
        pass

class UpdateBaseJob(MagentoJob):

    idxs = []

    @property
    def updates(self):
        return []

    def do_update(self, r, updates):

        # Only push stuff in the public store
        if self.is_public_store(r):

            # Get the object
            o = r.getObject()

            # Make the provided updates
            for (k,v) in updates.iteritems():
                setattr(o, k, v)

            # Reindex the object
            if self.idxs:
                self.portal_catalog.catalog_object(o, idxs=self.idxs)

    def run(self):

        for (r, _updates) in self.updates:
            try:
                self.do_update(r, _updates)
            except:
                self.log(u"Failed product update for %s %s: %r" % (
                    safe_unicode(r.Type),
                    safe_unicode(r.Title),
                    updates)
                )

# For products whose expiration date has passed, flip them to the "Expired" status.
class SetMagentoInfo(UpdateBaseJob):

    title = "Set Magento SKU/URL"

    priority = 1

    idxs = ['MagentoURL', 'SKU']

    @property
    def updates(self):

        # Get all products from Magento
        results = self.portal_catalog.searchResults({
            'UID' : self.plone_ids,
            'object_provides' : 'agsci.atlas.content.behaviors.IAtlasInternalMetadata',
        })

        for r in results:

            _ = self.by_plone_id(r.UID)

            if not _:
                continue

            # Holds attributes to be updated
            _updates = {}

            # Plone Product Values
            sku = r.SKU
            magento_url = r.MagentoURL

            # Magento Product Values
            _sku = _.get('sku')
            _magento_url = _.get('magento_url')

            # If Plone doesn't match Magento
            if _magento_url != magento_url or _sku != sku:

                if _magento_url and magento_url != _magento_url:

                    self.log(u"Set Magento URL to %s for %s %s" % (
                        _magento_url,
                        safe_unicode(r.Type),
                        safe_unicode(r.Title))
                    )

                    _updates['magento_url'] = _magento_url

                if _sku and sku != _sku:

                    self.log(u"Set SKU to %s for %s %s" % (
                        _sku,
                        safe_unicode(r.Type),
                        safe_unicode(r.Title))
                    )

                    _updates['sku'] = _sku

                # If the object was modified, return that data.
                if _updates:
                    yield (r, _updates)


# Generic 'repush' job that handles the reindexing
class RepushBaseJob(MagentoJob):

    @property
    def products(self):
        return []

    def run(self):
        for r in self.products:

            # Only push stuff in the public store
            if self.is_public_store(r):

                o = r.getObject()

                # Reindex the object
                o.reindexObject()

# Since Event Groups have counties listed, these will only be updated when the Event Group is imported.
class UpdateEventGroupCounties(RepushBaseJob):

    title = 'Update Event Group Counties'

    priority = 2

    @property
    def products(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
            'review_state' : ['published',],
            'modified' : self.modified_crit,
        })

        for r in results:

            _ = self.by_plone_id(r.UID) # Get Magento data

            if _:

                o = r.getObject()

                # Plone
                counties = EventGroupCountyDataAdapter(o).counties

                if not counties:
                    counties = []

                counties = tuple(sorted(counties))

                # Magento
                _counties = _.get('county', None)

                if not _counties:
                    _counties = []

                _counties = tuple(sorted(_counties))

                # If we have a Plone *or* Magento value
                if _counties or counties:

                    # And they don't match
                    if _counties != counties:

                        self.log(u"Updating counties for %s %s from %r to %r" % (
                                safe_unicode(r.Type),
                                safe_unicode(r.Title),
                                _counties,
                                counties
                            )
                        )

                        yield r

# Re-push updated products
class RepushUpdatedProducts(RepushBaseJob):

    title = 'Re-push updated products'

    @property
    def products(self):

        results = self.portal_catalog.searchResults({
            'review_state' : ['published-inactive', 'published',],
            'UID' : self.plone_ids,
            'modified' : self.modified_crit,
        })

        for r in results:

            _ = self.by_plone_id(r.UID) # Get Magento data

            if _:

                updated_at = r.modified.toZone(DEFAULT_TIMEZONE)
                _updated_at = DateTime(_.get('updated_at') + ' ' + DEFAULT_TIMEZONE)
                _diff = updated_at - _updated_at

                if _diff > self.grace_period/24.0:

                    self.log("Reimporting %s %s because updated_at [Plone] %s vs. [Magento] %s" % (
                            safe_unicode(r.Type),
                            safe_unicode(r.Title),
                            updated_at,
                            _updated_at,
                        )
                    )

                    yield r

# Re-push missing products
class RepushMissingProducts(RepushBaseJob):

    title = 'Re-push missing products'

    @property
    def products(self):

        results = self.portal_catalog.searchResults({
            'review_state' : ['published-inactive', 'published',],
            'object_provides' : [
                'agsci.atlas.content.IAtlasProduct',
                'agsci.person.content.person.IPerson'
            ],
            'modified' : self.modified_crit,
        })

        for r in results:

            _ = self.by_plone_id(r.UID) # Get Magento data

            if not _:

                if self.is_public_store(r):

                    self.log("Reimporting missing product %s %s" % (
                            safe_unicode(r.Type),
                            safe_unicode(r.Title),
                        )
                    )

                    yield r

# Re-push stale products
class RepushStaleProducts(RepushBaseJob):

    title = 'Re-push stale products'

    limit = 25

    def updated_at(self, uid):
        return self.by_plone_id(uid).get('updated_at', '9999')

    @property
    def products(self):

        # Get all active products in Magento
        results = self.portal_catalog.searchResults({
            'review_state' : ['published-inactive', 'published',],
            'object_provides' : [
                'agsci.atlas.content.IAtlasProduct',
                'agsci.person.content.person.IPerson'
            ],
            'modified' : self.modified_crit,
            'UID' : self.plone_ids,
        })

        # Sort by updated date in Magento
        results = sorted(results, key=lambda x: self.updated_at(x.UID), reverse=False)

        # Set counter
        counter = 0

        # Only grab limit products
        for r in results:

            if self.is_public_store(r):
                counter = counter + 1

                self.log("Reimporting stale product %s %s (Last updated %s)" % (
                        safe_unicode(r.Type),
                        safe_unicode(r.Title),
                        self.updated_at(r.UID),
                    )
                )

                yield r

            if counter >= self.limit:
                break