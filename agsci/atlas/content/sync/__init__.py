from bs4 import BeautifulSoup
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

try:
    from htmlentitydefs import codepoint2name
except:
    from html.entities import codepoint2name

import re

try:
    from urllib.request import urlopen # Python 3
except ImportError:
    from urllib2 import urlopen # Python 2

content_disposition_filename_re = re.compile(r'filename="(.*?)"', re.I|re.M)

external_reference_tags =[
    ('a', 'href'),
    ('img', 'src'),
]

# Class to hold json data and return as attributes
class json_data_object(object):

    def __init__(self, data={}):

        self.data = data

    def __getattribute__(self, name):

        # Don't proxy the 'data' attribute
        if name == 'data':
            return object.__getattribute__(self, name)

        # Make the 'contents' key return a list of uids
        if name == 'contents':
            try:
                return [x.get('uid') for x in self.data.get('contents')]
            except TypeError:
                return []

        # Otherwise, return the value of the key in the data dict
        if name in self.data:
            return self.data.get(name, '')

        # Then get the attribute on the object itself, or return blank on error
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return ''

# Base class for generic content importing

class BaseContentImporter(object):

    @property
    def registry(self):
        return getUtility(IRegistry)

    @property
    def data(self):
        if not hasattr(self, 'json_data_object'):
            self.json_data_object = json_data_object(self.get_data())

        return self.json_data_object

    def get_data(self):
        return {}

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
        for (k,v) in codepoint2name.items():

            if v in ["gt", "lt", "amp", "bull", "quot"]:
                continue

            html = html.replace(unichr(k), "&%s;" % v)

        # Replace <br /> inside table th/td with nothing.
        replaceEmptyBR = re.compile(r'(<(td|th).*?>)\s*(<br */*>\s*)+\s*(</\2>)', re.I|re.M)
        html = replaceEmptyBR.sub(r"\1 \4", html)

        # Remove HTML elements that only have a <br /> inside them
        removeEmptyBR = re.compile(r'(<(p|div|strong|em)>)\s*(<br */*>\s*)+\s*(</\2>)', re.I|re.M)
        html = removeEmptyBR.sub(r" ", html)

        # Remove attributes that should not be transferred
        removeAttributes = re.compile(r'\s*(id|width|height|valign|type|style|target|dir)\s*=\s*".*?"', re.I|re.M)
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
        soup = BeautifulSoup(html, features="lxml")

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

    def data_to_image_field(self, data, contentType='', filename=None):

        if filename:
            filename = filename.decode('utf-8')

        field = NamedBlobImage(filename=filename)
        field.data = data

        return field

    def data_to_file_field(self, data, contentType='', filename=None):

        if filename:
            filename = filename.decode('utf-8')

        field = NamedBlobFile(filename=filename, contentType=contentType)
        field.data = data

        return field

    # Takes a URL as a parameter
    # Returns data, mimetype, filename (if provided)
    def get_binary_data(self, url):

        # Open URL
        v = urlopen(url)

        # Determine filename
        filename = None

        try:
            m = content_disposition_filename_re.search(v.headers.get('content-disposition'))
        except TypeError:
            # No content disposition provided, regex will bomb
            pass
        else:
            if m:
                filename = m.group(1)

        # Return tuple of (data, contentType, filename)
        return (v.read(), v.headers.get('content-type'), filename)


# Content Importer class for content where JSON is provided as input, rather
# than pulled from a remote URL.
class SyncContentImporter(BaseContentImporter):

    def __init__(self, json_data):
        self.json_data = json_data

    def get_data(self):
        return self.json_data
