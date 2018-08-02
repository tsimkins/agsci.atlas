from datetime import datetime, timedelta

import pickle
import json
import redis
import requests

from .constants import CMS_DOMAIN

class CachedJSONData(object):

    # URL for JSON data
    DATA_URL = u""

    # Redis cache key
    redis_cachekey = u""

    # Timeout for cache
    CACHED_DATA_TIMEOUT = 86400 # One day

    # Data type for verification
    DATA_TYPE = (dict, list)

    @property
    def redis(self):
        return redis.StrictRedis(host='localhost', port=6379, db=0)

    # Downloads the JSON data
    def download_data(self):

        try:
            return requests.get(self.DATA_URL).json()

        except:
            return []

    @property
    def data(self):

        # Get the cached value
        data = self.redis.get(self.redis_cachekey)

        # If it's a string, unpickle
        if data and isinstance(data, (str, unicode)):
            data = pickle.loads(data)

        # Type and non-empty verification for data
        if isinstance(data, self.DATA_TYPE) and data:

            # Return value for data
            return data

        else:

            # Download GA data
            data = self.download_data()

            # If we have good data, store it
            if isinstance(data, self.DATA_TYPE) and data:

                # Set timeout
                timeout = timedelta(seconds=self.CACHED_DATA_TIMEOUT)

                # Store data in redis
                self.redis.setex(self.redis_cachekey, timeout, pickle.dumps(data))

                return data

        # Empty value
        return []

    @property
    def now(self):
        return datetime.now()


class GoogleAnalyticsData(CachedJSONData):

    # URL for JSON data from GA
    DATA_URL = "http://%s/google-analytics" % CMS_DOMAIN

    # Data type for verification
    DATA_TYPE = (list,  )

    # Redis cache key
    redis_cachekey = 'GOOGLE_ANALYTICS_DEFAULT_CACHEKEY'

class GoogleAnalyticsBySKU(GoogleAnalyticsData):

    # URL for JSON data from GA
    DATA_URL = "http://%s/google-analytics/sku" % CMS_DOMAIN

    # Redis cache key
    redis_cachekey = 'GOOGLE_ANALYTICS_SKU'

    def ga_data(self, days=60):

        data = {}

        # https://stackoverflow.com/questions/993358/creating-a-range-of-dates-in-python
        date_list = [self.now - timedelta(days=x) for x in range(0, days)]
        datestamps = set([x.strftime('%Y-%m') for x in date_list])

        for _ in self.data:

            sku = _.get('sku', None)

            if sku:
                values = _.get('values', [])

                for __ in values:

                    month = __.get('period', None)

                    if month in datestamps:
                        v = __.get('count', 0)

                        if not data.has_key(sku):
                            data[sku] = 0

                        data[sku] = data[sku] + int(v)

        return data

class GoogleAnalyticsBySecondaryCategory(GoogleAnalyticsData):

    # URL for JSON data from GA
    DATA_URL = "http://%s/google-analytics/category/secondary" % CMS_DOMAIN

    # Redis cache key
    redis_cachekey = 'GOOGLE_ANALYTICS_SECONDARY_CATEGORY'

    def ga_data(self, days=120):

        data = dict([(x, {}) for x in (1,2)])

        # https://stackoverflow.com/questions/993358/creating-a-range-of-dates-in-python
        date_list = [self.now - timedelta(days=x) for x in range(0, days)]
        datestamps = set([x.strftime('%Y-%m') for x in date_list])

        for _ in self.data:

            level = _.get('level', None)

            if level in data.keys():
                values = _.get('values', [])

                for __ in values:

                    category = __.get('category', None)
                    _values = __.get('values', [])

                    for ___ in _values:

                        sku = ___.get('sku', None)
                        __values = ___.get('values', [])

                        for ____ in __values:

                            month = ____.get('period', None)

                            if month in datestamps:
                                v = ____.get('count', 0)

                                if not data[level].has_key(category):
                                    data[level][category] = {}

                                if not data[level][category].has_key(sku):
                                    data[level][category][sku] = 0

                                data[level][category][sku] = data[level][category][sku] + int(v)

        return data

class GoogleAnalyticsTopProductsByCategory(GoogleAnalyticsData):

    def __init__(self, category=None, level=None):
        self.category = category
        self.level = level

    # URL for JSON data from GA
    @property
    def DATA_URL(self):
        return "http://%s/google-analytics/category/top/level/%d" % (CMS_DOMAIN, self.level)

    # Redis cache key
    @property
    def redis_cachekey(self):
        return 'GOOGLE_ANALYTICS_TOP_PRODUCTS_CATEGORY_LEVEL_%d' % self.level

    def ga_data(self):

        data = {}

        for _ in self.data:

            level = _.get('level', None)

            if level == self.level:
                values = _.get('values', [])

                for __ in values:

                    category = __.get('category', None)

                    if category == self.category:

                        _values = __.get('values', [])

                        for ___ in _values:

                            sku = ___.get('sku', None)
                            __values = ___.get('values', [])

                            for ____ in __values:

                                month = ____.get('period', None)

                                v = ____.get('count', 0)

                                if not data.has_key(sku):
                                    data[sku] = {}

                                data[sku][month] = v

            return data

class GoogleAnalyticsByCategory(GoogleAnalyticsData):

    def __init__(self, category=None, level=None):
        self.category = category
        self.level = level

    # URL for JSON data from GA
    @property
    def DATA_URL(self):
        return "http://%s/google-analytics/category/level/%d" % (CMS_DOMAIN, self.level)

    # Redis cache key
    @property
    def redis_cachekey(self):
        return 'GOOGLE_ANALYTICS_CATEGORY_LEVEL_%d' % self.level

    def ga_data(self):

        data = {}

        for _ in self.data:

            level = _.get('level', None)

            if level == self.level:
                values = _.get('values', [])

                for __ in values:

                    category = __.get('category', None)

                    if category == self.category:

                        _values = __.get('values', [])

                        for ___ in _values:

                            month = ___.get('period', None)

                            data[month] = {
                                'sessions' : ___.get('sessions', 0),
                                'users' : ___.get('users', 0)
                            }

            return data

# Not GA, but the easiest place to put it
class EPASMapping(CachedJSONData):

    # URL for JSON data
    DATA_URL = u"http://%s/magento/epas-mapping.json" % CMS_DOMAIN

    # Redis cache key
    redis_cachekey = u"EPAS_MAPPING_CACHEKEY"

    # Timeout for cache
    CACHED_DATA_TIMEOUT = 86400 # One day