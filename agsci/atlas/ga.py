from datetime import datetime, timedelta

import pickle
import json
import redis
import urllib2

GA_DATA_URL = "http://r39JxvLi.cms.extension.psu.edu/google-analytics/sku"

class GoogleAnalyticsBySKU(object):

    # Redis cache key
    redis_cachekey = 'GOOGLE_ANALYTICS_SKU'

    # Timeout for cache
    CACHED_DATA_TIMEOUT = 86400 # One day

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
            data = self.download_ga_data()

            # If we have good data, store it
            if isinstance(data, dict) and data:

                # Set timeout
                timeout = timedelta(seconds=self.CACHED_DATA_TIMEOUT)

                # Store data in redis
                self.redis.setex(self.redis_cachekey, timeout, pickle.dumps(data))

                return data

        # Empty value
        return {}

    # Downloads the JSON data by SKU (uncached)
    def download_ga_data(self):

        try:
            return json.loads(urllib2.urlopen(GA_DATA_URL).read())

        except:
            return {}

    def get_ga_data(self, days=60):

        data = {}

        # https://stackoverflow.com/questions/993358/creating-a-range-of-dates-in-python
        date_list = [self.now - timedelta(days=x) for x in range(0, days)]
        datestamps = set([x.strftime('%Y-%m') for x in date_list])

        for (sku, sku_data) in self.ga_data.iteritems():

            for (month, v) in sku_data.iteritems():

                if month in datestamps:

                    if not data.has_key(sku):
                        data[sku] = 0

                    data[sku] = data[sku] + int(v)

        return data

    @property
    def now(self):
        return datetime.now()