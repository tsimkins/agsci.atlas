from bs4 import BeautifulSoup
from plone.memoize.instance import memoize

try:
    from urllib.parse import urlparse # Python 3
except ImportError:
    from urlparse import urlparse # Python 2

from . import BaseContentImporter, external_reference_tags

try:
    from urllib.request import urlopen # Python 3
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, HTTPError, URLError # Python 2

import json



# Atlas product class for import from current Plone site
class AtlasProductImporter(BaseContentImporter):

    def __init__(self, uid=None, url=None, domain=None):
        self.uid = uid
        self.url = url
        self.domain = domain

    @property
    def root_url(self):
        if self.domain:
            url = 'http://%s' % self.domain
        else:
            url = self.registry.get('agsci.atlas.import.root_url')

        if url.endswith('/'):
            return url[:-1]

        return url

    # Calculate the URL for the API 'endpoint' depending on if this was called
    # with a UID or a URL
    def get_api_url(self):

        if self.uid:
            return '%s/@@api-json?UID=%s&full=true' % (self.root_url, self.uid)

        if self.url and self.url.startswith(self.root_url):
            return '%s/@@api-json?full=true' % (self.url,)

        raise Exception('API Error: No valid API URL calculated.')

    # Returns the domain of the API URL
    def get_api_domain(self):
        url = self.get_api_url()
        return urlparse(url).netloc

    @memoize
    def get_data(self):

        url = self.get_api_url()

        try:
            data = urlopen(url).read()
        except (URLError, HTTPError):
            raise Exception('API Error: Cannot download data from "%s"' % url)

        json_data = json.loads(data)

        # Check for empty results
        if not json_data:
            raise Exception('API Error: No object found at "%s"' % url)

        # Scrub HTML
        if 'html' in json_data:
            json_data['html'] = self.scrub_html(json_data.get('html'))

            # Get Image and file references from html
            soup = BeautifulSoup(json_data['html'])

            for (i,j) in external_reference_tags:

                for k in soup.findAll(i):
                    url = k.get(j, '')

                    if url:
                        if i not in json_data:
                            json_data[i] = []

                        json_data[i].append(url)

        # Put leadimage data into field
        if json_data.get('has_content_lead_image', False):

            image_data = self.get_binary_data(json_data.get('image_url', ''))

            if image_data:
                json_data['leadimage'] = image_data[0]
                json_data['leadimage_content_type'] = image_data[1]
                json_data['leadimage_filename'] = image_data[2]

        return json_data

