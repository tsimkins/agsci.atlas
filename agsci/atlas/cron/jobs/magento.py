from Acquisition import aq_base
from bs4 import BeautifulSoup
from DateTime import DateTime
from Products.CMFPlone.utils import safe_unicode
from datetime import timedelta
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest

import Missing
import random
import requests

import re

from agsci.atlas.constants import DEFAULT_TIMEZONE, MAGENTO_DATA_URL, MAGENTO_CATEGORIES_URL, \
                                  TOOLS_DOMAIN, UID_RE
from agsci.atlas.content.adapters import EventGroupCountyDataAdapter, \
                                         EventGroupCreditDataAdapter
from agsci.atlas.utilities import ploneify

from .. import CronJob

class MagentoJob(CronJob):

    MAGENTO_DATA_URL = MAGENTO_DATA_URL
    MAGENTO_CATEGORIES_URL = MAGENTO_CATEGORIES_URL

    cache_key = 'MAGENTO_DATA'

    keys = [
        'plone_id',
        'magento_url',
        'sku',
    ]

    def m2_api(self, plone_id):

        if UID_RE.match(plone_id):

            url = "https://%s/m2/products/plone_id/%s" % (TOOLS_DOMAIN, plone_id)

            response = requests.get(url)

            if response.status_code in (200,):

                _ = response.json()
                if _ and isinstance(_, (list,)):
                    return _ [0]

        return {}

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
    def modified_time(self):
        return DateTime() - (self.grace_period/24.0)

    @property
    def modified_crit(self):

        return {
            'query' : self.modified_time,
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

        if key not in cache:

            _ = {}

            for i in self._data:
                if not i.get('product_status', None) == u'Enabled':
                    continue
                for k in self.keys:
                    if k not in _:
                        _[k] = {}
                    v = i.get(k, None)
                    if v:
                        _[k][v] = i

            _['categories'] = {}

            for _c in self._category_data.values():

                # Adjust Level
                if 'level' in _c:
                    _c['level'] = int(_c['level']) - 1
                    _c['product_type'] = 'CategoryLevel%d' % _c['level']

                # Fix description shenanigans
                if 'description' in _c and _c['description'] and isinstance(_c['description'], (unicode, str)):

                    if '<' in _c['description']:
                        soup = BeautifulSoup(_c['description'])
                        _c['description'] = soup.text

                    for (_f, _t) in [
                        (u"\u2019", u"'"),
                        (u"\\n", " "),
                    ]:
                        _c['description'] = _c['description'].replace(_f, _t).strip()

                # Key from Plone Value
                if _c['plone_value']:
                    _['categories'][_c['plone_value']] = _c

            cache[key] = _

        return cache[key]

    def get_json_data(self, URL):
        try:
            response = requests.get(URL)
            return response.json()

        except:
            return []

    # Downloads the JSON data by SKU (uncached)
    @property
    def _data(self):
        return self.get_json_data(self.MAGENTO_DATA_URL)

    # Downloads the JSON category data (uncached)
    @property
    def _category_data(self):
        return self.get_json_data(self.MAGENTO_CATEGORIES_URL)

    @property
    def all_products(self):
        return self.data.get('plone_id', {}).values()

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

    def get_category(self, v):
        return self.data.get('categories', {}).get(v, {})

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
            for (k,v) in updates.items():
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

    idxs = ['MagentoURL', 'SKU', 'SearchableText', 'ContentErrorCodes', 'ContentIssues']

    @property
    def updates(self):

        # Get all products from Magento
        results = self.portal_catalog.searchResults({
            'UID' : self.plone_ids,
            'object_provides' : 'agsci.atlas.content.behaviors.IAtlasInternalMetadata',
        })

        for r in results:

            # Only set stuff in the public store
            if not self.is_public_store(r):
                continue

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

# Since Event Groups have counties listed, these will only be updated when
# the Event Group is imported.
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

# Since Event Groups have credits as an attribute, these will only be updated
# when the Event Group is imported.
class UpdateEventGroupCredits(RepushBaseJob):

    title = 'Update Event Group Credits'

    priority = 2

    field = 'credit_type'

    def get_group_credit_info(self, o):
        return EventGroupCreditDataAdapter(o).credits

    @property
    def products(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : [
                'agsci.atlas.content.event.group.IEventGroup',
                'agsci.atlas.content.online_course.group.IOnlineCourseGroup',
            ],
            'review_state' : ['published',],
        })

        results = [x for x in results if x.IsExternalStore]

        for r in results:

            o = r.getObject()

            adapter_credits = self.get_group_credit_info(o)

            if adapter_credits:

                self.log(u"Child credits for %s %s are %r" % (
                        safe_unicode(r.Type),
                        safe_unicode(r.Title),
                        adapter_credits,
                    )
                )

                _credits = getattr(o, self.field, [])

                if not _credits:
                    _credits = []

                missing_credits = list(set(adapter_credits) - set(_credits))

                if missing_credits:

                    self.log(u"Updating credits for %s %s by adding %r for %r" % (
                            safe_unicode(r.Type),
                            safe_unicode(r.Title),
                            missing_credits,
                            _credits
                        )
                    )

                    yield r

    def run(self):

        for r in self.products:

            # Only push stuff in the public store
            if self.is_public_store(r):

                o = r.getObject()

                group_credits = self.get_group_credit_info(o)

                if group_credits:
                    setattr(o, self.field, group_credits)

                # Reindex the object
                o.reindexObject()

class UpdateEventGroupCreditCategories(UpdateEventGroupCredits):
    field = 'credit_category'

    title = 'Update Event Group Categories'

    def get_group_credit_info(self, o):
        return EventGroupCreditDataAdapter(o).credit_categories

# Re-push updated products
class RepushUpdatedProducts(RepushBaseJob):

    title = 'Re-push updated products'

    product_types = []

    @property
    def products(self):

        query = {
            'review_state' : ['published-inactive', 'published',],
            'UID' : self.plone_ids,
            'modified' : self.modified_crit,
        }

        if self.product_types:
            query['Type'] = self.product_types

        results = self.portal_catalog.searchResults(query)

        for r in results:

            _ = self.by_plone_id(r.UID) # Get Magento data

            if _:
                updated_at = r.modified.toZone(DEFAULT_TIMEZONE)
                _updated_at = DateTime(_.get('updated_at'))
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

# Re-push updated Cvent Events
class RepushUpdatedCventEvents(RepushUpdatedProducts):

    title = 'Re-push updated Cvent Events'

    grace_period = 3 # Event in Magento has not been updated within three hours
    max_modified = 6 # Modified more than six hours ago

    product_types = [u'Cvent Event',]

    @property
    def modified_time(self):
        return DateTime() - self.max_modified/24.0

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

# Re-push expired products
class RepushExpiredProducts(RepushBaseJob):

    title = 'Re-push expired products'

    @property
    def products(self):

        results = self.portal_catalog.searchResults({
            'review_state' : ['expired',],
            'object_provides' : [
                'agsci.atlas.content.IAtlasProduct',
            ],
            'UID' : self.plone_ids, # If it's in the Magento feed, it's live.
            'modified' : self.modified_crit,
        })

        for r in results:

            _ = self.by_plone_id(r.UID) # Get Magento data

            if _.get('product_status', None) in ['Enabled',]:

                if self.is_public_store(r):

                    self.log("Reimporting expired product %s %s" % (
                            safe_unicode(r.Type),
                            safe_unicode(r.Title),
                        )
                    )

                    yield r

# Re-push stale products
class RepushStaleProducts(RepushBaseJob):

    title = 'Re-push stale products'

    limit = 25

    grace_period = 24*14 # Two weeks

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

# Re-push missing child products (e.g. Workshops not associated with a Workshop Group
class RepushMissingChildProducts(RepushBaseJob):

    grace_period = 4

    title = 'Re-push missing child products'

    def getChildPloneIds(self, r):

        v = self.portal_catalog.searchResults({
            'IsChildProduct' : True,
            'review_state' : 'published',
            'path' : r.getPath(),
            'modified' : self.modified_crit,
        })

        return [x.UID for x in v]

    def getChildInfo(self, uids):

        return self.portal_catalog.searchResults({
            'IsChildProduct' : True,
            'review_state' : 'published',
            'UID' : uids,
            'sort_on' : 'start',
            'modified' : self.modified_crit,
        })

    @property
    def products(self):

        magento_plone_ids = self.plone_ids

        results = self.portal_catalog.searchResults({
            'review_state' : ['published',],
            'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
            'review_state' : 'published',
            'UID' : magento_plone_ids,
        })

        for r in results:

            child_plone_ids = self.getChildPloneIds(r)

            if child_plone_ids:

                _ = self.by_plone_id(r.UID)

                magento_child_plone_ids = _.get('child_plone_ids', [])

                missing_children = set(child_plone_ids) - set(magento_child_plone_ids)

                missing_children = list(set(magento_plone_ids) & missing_children)

                if missing_children:

                    self.log(u"%s %s missing %d children" % (
                            safe_unicode(r.Type),
                            safe_unicode(r.Title),
                            len(missing_children),
                        )
                    )

                    for _r in self.getChildInfo(missing_children):

                        _date = _r.start.strftime('%B %d, %Y %I:%M %p')

                        self.log(u"Reimporting %s %s (%s)" % (
                                safe_unicode(_r.Type),
                                safe_unicode(_r.Title),
                                _date,
                            )
                        )

                        yield _r

# Re-push products that have Conference/Workshop Groups with no upcoming
# Events set as a related item
class RepushInvalidRelatedProducts(RepushBaseJob):

    limit = 10

    title = 'Re-push products with invalid related products.'

    @property
    def invalid_skus(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
            'Type' : [
                'Workshop Group',
                'Conference Group',
            ],
            'review_state' : 'published',
        })

        return sorted(set([x.SKU for x in results if x.SKU and not x.HasUpcomingEvents]))

    @property
    def products(self):

        invalid_skus = set(self.invalid_skus)

        invalid_related = {}

        uids = []

        for _ in self.all_products:
            related_skus = set(_.get('related_skus', []))
            if related_skus:
                _invalid_related = list(related_skus & invalid_skus)
                if _invalid_related:
                    uids.append(_['plone_id'])
                    invalid_related[_['sku']] = _invalid_related

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ['expired', 'published'],
            'UID' : uids,
            'modified' : self.modified_crit,
        })

        if len(results) > self.limit:
            results = random.sample(results, self.limit)

        for r in results:

            self.log(u"Invalid Related Products. Repushing %s %s %s. %r" % (
                r.SKU,
                safe_unicode(r.Type),
                safe_unicode(r.Title),
                invalid_related.get(r.SKU, [])
            ))

            yield r


# Updates Plone short names to normalized title
class FixPloneShortNames(MagentoJob):

    limit = 10

    priority = 3

    title = u'Fix Plone short names'

    product_types = [
        u'Webinar Group',
        u'Online Course Group',
        u'Smart Sheet',
        u'App',
        u'Workshop Group',
        u'Learn Now Video',
        u'Article',
        u'News Item',
        u'Conference Group'
    ]

    def run(self):

        results = self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'IsChildProduct' : [None, False],
            'review_state' : ['published',],
            'Type' : self.product_types
        })

        # Counter for updated products
        counter = 0

        # Iterate through results
        for r in results:

            # Stop after updating N products
            if counter > self.limit:
                break

            # Normalized title
            _id = ploneify(r.Title)

            valid_ids = [_id,]

            # For Articles, the short URL should *always* match the normalized
            # Title. For anything else, the Magento URL is fine, too.
            if r.Type not in [u'Article']:
                valid_ids = [_id,]
                magento_url = r.MagentoURL

                if magento_url:
                    valid_ids.append(magento_url)

            # Get it down to a set of valid values
            valid_ids = list(set(valid_ids))

            # If our id is not valid
            if r.getId not in valid_ids:

                # ... and there's only one valid value
                if len(valid_ids) == 1:

                    # Get the id as a string
                    to_id = safe_unicode(valid_ids[0]).encode('utf-8')

                    # Get the object and parent object
                    o = r.getObject()
                    p = o.aq_parent

                    # Validate that we're not duplicating an existing id
                    if to_id not in p.objectIds():

                        # Increment the counter
                        counter = counter +1

                        # Log message
                        self.log(u"Updated Plone Short Name for %s %s from '%s' to '%s'" % (
                            safe_unicode(r.Type),
                            safe_unicode(r.Title),
                            r.getId,
                            to_id,)
                        )

                        # Actually rename object
                        p.manage_renameObjects(ids=[r.getId], new_ids=[to_id])
