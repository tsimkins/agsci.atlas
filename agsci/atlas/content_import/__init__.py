from zope.component import getUtility
from plone.registry.interfaces import IRegistry
import json
import urllib2
import re
from plone.memoize.instance import memoize
from BeautifulSoup import BeautifulSoup
import htmlentitydefs
from zope.component.hooks import getSite
from plone.namedfile.file import NamedBlobImage

# Regular expression to validate UID

uid_re = re.compile("^[0-9abcedf]{32}$", re.I|re.M)

# Exceptions for import process

class APIError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


# Class to hold json data and return as attributes
class json_data_object(object):

    def __init__(self, data={}):

        self.data = data

    def __getattribute__(self, name):

        if name == 'data':
            return object.__getattribute__(self, name)

        if self.data.has_key(name):
            return self.data.get(name, '')

        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return ''


# Parent class for import from current Plone site

class AtlasContentImporter(object):

    def __init__(self, uid=None):

        # Validate UID
        if not uid_re.match(uid):
            raise ValueError('Invalid UID %s' % uid)

        self.uid = uid

    @property
    def registry(self):
        return getUtility(IRegistry)

    @property
    def root_url(self):
        url = self.registry.get('agsci.atlas.import.root_url')

        if url.endswith('/'):
            return url[:-1]

        return url
    
    @property
    def import_path(self):
        path = self.registry.get('agsci.atlas.import.path')

        if path.startswith('/'):
            path = path[1:]

        return getSite().restrictedTraverse(path)
        

    @property
    def data(self):
        if not hasattr(self, 'json_data_object'):
            self.json_data_object = json_data_object(self.get_data())

        return self.json_data_object

    @memoize
    def get_data(self):
        url = '%s/@@api-json?UID=%s&full=true' % (self.root_url, self.uid)

        try:
            data = urllib2.urlopen(url).read()
        except (urllib2.URLError, urllib2.HTTPError):
            raise APIError('Cannot download data from %s' % url)

        json_data = json.loads(data)

        # Scrub HTML
        if json_data.has_key('html'):
            json_data['html'] = self.scrub_html(json_data.get('html'))

        # Put leadimage data into fields
        if json_data.get('has_content_lead_image', '') == 'true':
        
            image_data = self.get_leadimage(json_data.get('image_url', ''))
            
            if image_data:
                json_data['leadimage'] = image_data

        return json_data

    def image_data_to_object(self, image_data):
        image = NamedBlobImage()
        image.data = image_data
        return image

    def get_leadimage(self, image_url):

        return urllib2.urlopen(image_url).read()

    def scrub_html(self, html):

        # Clean up whitespace, and make everything space delimited
        html = " ".join(html.split())

        # HTML entites to turn into ASCII.
        htmlEntities = [
            ["&#8211;", "--"],
            ["&#8220;", '"'],
            ["&#8221;", '"'],
            ["&#8216;", "'"],
            ["&#8217;", "'"],
            ["&#145;", "'"],
            ["&#146;", "'"],
            ["&#160;", " "],
            ["&nbsp;", " "],
            ["&bull;", " "],
            ["&quot;", "\""],
            ["&#150;", "-"],
            ["&#151;", " -- "],
            ["&#147;", "\""],
            ["&#148;", "\""],
            ["&quot;", "\""],
            ["&quot;", "\""],
            [unichr(186), "&deg;"],
            [unichr(176), "&deg;"],
            [unichr(215), "x"],
            ["`", "'"],
            [unichr(181), "&micro;"],
            [unichr(8776), "&asymp;"],
            [unichr(160), " "],
            ["\t", " "],
            [u"\u201c", '"'],
            [u"\u201d", '"'],
            [u"\u2018", "'"],
            [u"\u2019", "'"],
            [u"\u2013", "-"],
            [u"\u2014", "--"],
        ]

        # Replace those entites
        for ent in htmlEntities:
            html = html.replace(ent[0], ent[1])

        # Replace unicode characters (u'\u1234') with html entity ('&abcd;')
        for (k,v) in htmlentitydefs.codepoint2name.iteritems():

            if v in ["gt", "lt", "amp", "bull", "quot"]:
                continue

            html = html.replace(unichr(k), "&%s;" % v)

        # Regex to replace multiple <br /> tags with one
        replaceDuplicateBR = re.compile(r'(<p.*?>)(.*?)(<br */*>\s*){2,10}(.*?)(</p>)', re.I|re.M)

        # Replace <br /> inside table th/td with nothing.
        replaceEmptyBR = re.compile(r'(<(td|th).*?>)\s*(<br */*>\s*)+\s*(</\2>)', re.I|re.M)
        html = replaceEmptyBR.sub(r"\1 \4", html)

        # Remove HTML elements that only have a <br /> inside them
        removeEmptyBR = re.compile(r'(<(p|div|strong|em)>)\s*(<br */*>\s*)+\s*(</\2>)', re.I|re.M)
        html = removeEmptyBR.sub(r" ", html)

        # Remove attributes that should not be transferred
        removeAttributes = re.compile('\s*(id|width|height|valign|type|style|target|dir)\s*=\s*".*?"', re.I|re.M)
        html = removeAttributes.sub(" ", html)

        # Remove empty tags
        removeEmptyTags = re.compile(r'<(p|span|strong|em)>\s*</\1>', re.I|re.M)
        html = removeEmptyTags.sub(" ", html)

        # Remove HTML comments
        removeComments = re.compile(r'<!--(.*?)-->', re.I|re.M)
        removeCommentsEncoded = re.compile(r'&lt;!--(.*?)--&gt;', re.I|re.M)

        html = removeComments.sub(" ", html)
        html = removeCommentsEncoded.sub(" ", html)

        # Into soup
        soup = BeautifulSoup(html)

        # TODO: Remove unused classes, only leave valid classes

        # Get back formatted HTML

        html = repr(soup).decode("utf-8")

        # Deal with whitespace issues

        html = re.sub('\s+', ' ', html.replace('\n', ' '))
        html = html.replace(' </a>', '</a> ')
        html = re.sub('\s+', ' ', html.replace('\n', ' '))

        for x in ".,?!":
            html = html.replace(' %s' % x, "%s " % x)
            html = html.replace('</a> %s' % x, "</a>%s " % x)
            html = html.replace(' %s' % x, "%s " % x)

        # Return of scrubbed HTML
        return html


