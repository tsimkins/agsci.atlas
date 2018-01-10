from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

from datetime import datetime, timedelta

import pickle
import random
import redis
import urllib2

from . import BaseAtlasAdapter

from ..structure import IAtlasStructure
from ..vocabulary.calculator import AtlasMetadataCalculator

GA_DATA_URL = "http://r39JxvLi.cms.extension.psu.edu/google-analytics"

class BaseRelatedProductsAdapter(BaseAtlasAdapter):

    # Items to return
    item_count = 10

    # These should add up to 100
    item_breakdown = {
        'WSP-G' : 30,
        'AGRS' : 30,
        'OLC-G' : 20,
        'VID' : 10,
        'ART' : 10,
    }

    # Default item type to 'fill' missing slots
    item_default = 'ART'

    # Multiplier for the number of items required to create a pool for
    # random selection
    item_pool_size = 3

    # Redis cache key
    redis_cachekey = 'GOOGLE_ANALYTICS_SKU'

    # Timeout for cache
    CACHED_DATA_TIMEOUT = 86400 # One day

    # Default SKU pattern
    @property
    def valid_patterns(self):
        return tuple(['%s-' % x for x in self.item_breakdown.keys()])

    @property
    def redis(self):
        return redis.StrictRedis(host='localhost', port=6379, db=0)

    @property
    def ga_data(self):

        # Get the cached value
        data = self.redis.get(self.redis_cachekey)

        # If it's a string, unpickle
        if data and isinstance(data, (str, unicode)):
            data = pickle.loads(data)

        # Type and non-empty verification for data
        if isinstance(data, dict) and data:

            # Return value for data
            return data

        else:

            # Download GA data
            data = self.get_ga_data

            # If we have good data, store it
            if isinstance(data, dict) and data:

                # Set timeout
                timeout = timedelta(seconds=self.CACHED_DATA_TIMEOUT)

                # Store data in redis
                self.redis.setex(self.redis_cachekey, timeout, pickle.dumps(data))

                return data

        # Empty value
        return {}

    @property
    def now(self):
        return datetime.now()

    @property
    def get_ga_data(self):

        data = {}

        # https://stackoverflow.com/questions/993358/creating-a-range-of-dates-in-python
        date_list = [self.now - timedelta(days=x) for x in range(0, 60)]
        datestamps = set([x.strftime('%Y-%m') for x in date_list])

        for i in datestamps:
            URL = "%s/%s.tsv" % (GA_DATA_URL, i)

            try:
                _ = urllib2.urlopen(URL).read()
                _ = [x.split("\t") for x in _.strip().split("\n")]
            except:
                continue
            else:
                for (_y, _m, sku, v) in _:
                    if not data.has_key(sku):
                        data[sku] = 0
                    data[sku] = data[sku] + int(v)

        return data


    @property
    def parent_category(self):

        for o in self.context.aq_chain:

            if IPloneSiteRoot.providedBy(o):
                break

            elif IAtlasStructure.providedBy(o):
                return o

    def all_related_skus(self, level=None):

        # Return value
        rv = []

        # This is the level that was passed in.  Storing it in another variable
        # because a default value of "None" results in the parent's level value
        # being used, but the category level is set to *only* the parent's
        # category.  A subsequent call will do all category values at the
        # parent's level.
        initial_level = level

        # Query values
        category_level = []

        # No level passed in, use the parent's value only.
        if not level:

            # Get the parent category object
            parent_category = self.parent_category

            # If we're inside a category
            if parent_category:

                # Grab the numeric level from the type. This is cheating, because
                # we're just grabbing the '3' from 'CategoryLevel3' as a substring.
                parent_category_type = parent_category.Type()
                level = int(parent_category_type[-1])

                # Do a +1 (e.g. L3 to a non-existant L4) so it can be decremented.
                initial_level = level + 1

                # Instantiate a metadata calculator calculator based on the
                # parent type, and get the full category value.
                mc = AtlasMetadataCalculator(parent_category_type)
                v = mc.getMetadataForObject(parent_category)

                # If we have a valid category value,
                if v:
                    category_level = [v,]

        else:
            category_level = getattr(self.context, 'atlas_category_level_%d' % level, [])

        if category_level:

            results = self.portal_catalog.searchResults({
                'CategoryLevel%d' % level : category_level,
                'object_provides' : 'agsci.atlas.content.IAtlasProduct',
                'review_state' : 'published',
            })

            # Filter out child products
            results = [x for x in results if not x.IsChildProduct]

            # Get a list of SKUs
            skus = [x.SKU for x in results if x.SKU]

            # Filter by only valid patterns
            skus = [x for x in skus if x.startswith(self.valid_patterns)]

            # Remove own SKU from list
            own_sku = getattr(self.context, 'sku', None)

            if own_sku in skus:
                skus.remove(own_sku)

            # If we're at L3, and we don't have enough results, grab the matching Level 2
            # Same for L2...L1, if we get that far.
            if initial_level > 1:
                if len(skus) < self.item_pool_size*self.item_count:
                    skus.extend(self.all_related_skus(initial_level-1))

            # Make this a unique list
            rv = list(set(skus))

        return rv

    def pick_items(self, sku_pattern, item_count, related_skus, ga_data):

        rv = []

        filtered_ga_data = [(k,v) for (k,v) in ga_data.iteritems() if k.startswith('%s-' % sku_pattern)]

        filtered_ga_data = [(k,v) for (k,v)in filtered_ga_data if k in related_skus]

        filtered_ga_data.sort(key=lambda x: x[1], reverse=True)

        # All product count
        all_traffic = len(filtered_ga_data)

        # Top 50% of product count
        top_traffic = int(all_traffic/2.0)

        # If we have more in the top 50%, return a random sample of item_count
        # just from the top 50%
        if top_traffic >= item_count:
            rv = random.sample(filtered_ga_data[:top_traffic], item_count)

        # If we still have more potential items than we need, take the top N items
        elif all_traffic >= item_count:
            rv = filtered_ga_data[:item_count]

        # Otherwise, return all items
        else:
            rv = list(filtered_ga_data)

        # Return the SKU
        return [x[0] for x in rv]

    @property
    def calculated_related_skus(self):

        # Return value
        rv = []

        # Get all possible related SKUs
        related_skus = self.all_related_skus()

        # Get the SKU-keyed GA data
        ga_data = self.ga_data

        # Filter the related SKUs by the SKUs in the GA data
        related_skus = set(related_skus) & set(ga_data)

        # Iterate through the SKU types
        for (k,v) in self.item_breakdown.iteritems():
            item_count = int((v*self.item_count)/100.0)
            rv.extend(self.pick_items(k, item_count, related_skus, ga_data))

        # If we come up short, append items of the default type
        if len(rv) < self.item_count:

            # Grab item_count items, so we have enough
            default_item_skus = self.pick_items(self.item_default, self.item_count, related_skus, ga_data)

            # Remove already picked skus
            default_item_skus = list(set(default_item_skus) - set(rv))

            # How many are we missing?
            missing_count = self.item_count - len(rv)

            # If we've picked more than we're missing, include a random sample
            if len(default_item_skus) > default_item_skus:
                rv.extend(random.sample(default_item_skus, default_item_skus))

            # Otherwise, just throw on what we have
            else:
                rv.extend(default_item_skus)

        return rv

    def getData(self, **kwargs):

        return {
            'related_skus' : self.calculated_related_skus,
        }
