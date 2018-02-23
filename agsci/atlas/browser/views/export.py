from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import safe_unicode
from DateTime import DateTime
from copy import deepcopy
from datetime import datetime
from plone.memoize.view import memoize
from zope.component.hooks import getSite

import StringIO
import re
import xlwt
import zipfile

from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DELIMITER
from agsci.atlas.content.adapters import LocationAdapter
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.content.structure import ICategoryLevel1
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.counties import getSurroundingCounties
from agsci.atlas.ga import GoogleAnalyticsBySKU
from agsci.atlas.utilities import ploneify

from . import CategorySKURegexView
from .base import BaseView

class ProductResult(object):

    def __init__(self, r=None, **kwargs):
        self.r = r
        self.view = kwargs.get('view', None)
        self.category = kwargs.get('category', None)

    @property
    def context(self):
        return getSite()

    def scrub(self, x):
        if isinstance(x, (str, unicode)):
            return safe_unicode(" ".join(x.strip().split()))
        elif isinstance(x, bool):
            return {True : 'Yes', False : 'No'}.get(x, 'Unknown')
        elif isinstance(x, int):
            return x
        else:
            return repr(x)

    @property
    def widths(self):
        return [
            None, None, 20, 75, 100, 100, 10
        ]

    @property
    def headings(self):
        return [
            "UID",
            "Category",
            "Type",
            "Title",
            "Description",
            "URL",
            "Remove?",
        ]

    def toLocalizedTime(self, *args, **kwargs):
        return self.context.restrictedTraverse('@@plone').toLocalizedTime(*args, **kwargs)

    def inline_list(self, x):

        if x:
            if isinstance(x, (list, tuple)):
                return '; '.join(x)

            elif isinstance(x, (str, unicode)):
                return x

        return ''

    @property
    def data(self):
        return [
            self.scrub(x) for x in
            [
                self.r.UID,
                '',
                self.r.Type,
                self.r.Title,
                self.r.Description,
                self.r.getURL(),
                '',
            ]
        ]

class TopProductResult(ProductResult):

    @property
    def widths(self):
        return [
            None, None, 20, 75, 100, 100, 10, 11, 12, 11
        ]

    @property
    def headings(self):
        return [
            "UID",
            "Category",
            "Type",
            "Title",
            "Description",
            "URL",
            "Is Featured?",
            "Is Educational Driver?",
            "Unique Pageviews",
        ]

    @property
    def is_featured(self):
        o = self.r.getObject()
        return not not getattr(o, 'is_featured', False)

    @property
    def is_educational_driver(self):
        o = self.r.getObject()

        educational_drivers = getattr(o, 'atlas_educational_drivers', [])

        if educational_drivers:
            return not not [x for x in educational_drivers if x.startswith('%s%s' % (self.category, DELIMITER))]

        return False

    @property
    def data(self):

        return [
            self.scrub(x) for x in
            [
                self.r.UID,
                '',
                self.r.Type,
                self.r.Title,
                self.r.Description,
                self.r.getURL(),
                self.is_featured,
                self.is_educational_driver,
                self.view.ga_sku_data.get(self.r.SKU, 0)
            ]
        ]

class PersonResult(ProductResult):

    @property
    def headings(self):
        return [
            "UID",
            "Category",
            "Name",
            "Penn State Id",
            "Classifications",
            "URL",
            "Remove?",
        ]

    @property
    def data(self):

        return [
            self.scrub(x) for x in
            [
                self.r.UID,
                '',
                self.r.Title,
                self.r.getId,
                self.inline_list(self.r.Classifications),
                self.r.getURL(),
                '',
            ]
        ]

class EventResult(ProductResult):

    @property
    def headings(self):
        return [
            "Primary Category",
            "Event Type",
            "Title",
            "Description",
            "Date/Time",
            "County",
            "Address",
            "Phone",
            "Email",
            "Registration Deadline",
            "Price",
            "URL",
        ]

    @property
    def widths(self):
        return [
            30, 12, 50, 50, 52, 14, 78, 13, 26, 24, 10, 50
        ]

    def county(self, o):
        v = getattr(o, 'county', [])

        if not v:
            return ''

        return self.inline_list(v)

    def price(self, o):
        v = getattr(o, 'price', None)

        if not v:
            return 'Free'

        return '$%0.2f' % v

    def address(self, o):

        adapter = LocationAdapter(o)

        return adapter.full_address

    def magento_url(self, p):

        if IEventGroup.providedBy(p):
            magento_url = getattr(p, 'magento_url', '')

            if magento_url:
                return 'https://extension.psu.edu/%s' % magento_url

        return ''

    def registration_deadline(self, o):
        v = getattr(o, 'registration_deadline', None)

        if v:
            return self.toLocalizedTime(v, long_format=False)

        return ''

    def hide_product(self, o):
        return getattr(o, 'hide_product', False)

    # Gets the title of the L1 category
    def primary_category(self, o):
        for i in o.aq_chain:
            if ICategoryLevel1.providedBy(i):
                return i.Title()
            elif IPloneSiteRoot.providedBy(i):
                break
        return 'N/A'

    @property
    def data(self):

        r = self.r
        o = r.getObject()
        p = o.aq_parent

        if IEventGroup.providedBy(p) and not self.hide_product(p):

            return [
                self.scrub(x) for x in
                [
                    self.primary_category(p),
                    p.Type().replace(' Group', ''),
                    p.Title(),
                    p.Description(),
                    self.toLocalizedTime(r.start, end_time=r.end, long_format=True),
                    self.county(o),
                    self.address(o),
                    '877-345-0691',
                    'ExtensionSupport@psu.edu',
                    self.registration_deadline(o),
                    self.price(o),
                    self.magento_url(p),
                ]
            ]


class ExportProducts(BaseView):

    level = 3

    all = "All"

    mime_type = 'application/zip'

    report = "products"

    fields = ProductResult

    hidden_columns = [0,1]

    has_category = True

    @property
    def filename(self):
        return "%s-%s.zip" % (self.datestamp, self.report)

    @property
    def now(self):
        return datetime.now()

    @property
    def datestamp(self):
        return self.now.strftime('%Y%m%d_%H%M%S')

    @property
    def results(self):

        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'IsChildProduct' : False,
            'review_state' : ACTIVE_REVIEW_STATES,
        })

    def _terms(self, level, hidden=True):

        mc = AtlasMetadataCalculator('CategoryLevel%d' % level)
        v = [x.value for x in mc.getTermsForType()]

        if not hidden:
            hidden = mc.getHiddenTerms()
            v = [x for x in v if not x in hidden]

        return v

    @property
    def terms(self):

        _ = self._terms(self.level)

        if self.level > 1:
            _.extend(['%s%s%s' % (x, DELIMITER, self.all) for x in self._terms(self.level - 1)])

        return sorted(_)

    @property
    def data(self):

        data = dict([(x, {}) for x in self._terms(self.level - 1)])
        _data = dict([(x, []) for x in self.terms])

        results = self.results

        for r in results:
            l1 = 'CategoryLevel%d' % (self.level - 1)
            l2 = 'CategoryLevel%d' % self.level

            v1 = getattr(r, l1, [])
            v2 = getattr(r, l2, [])

            c = []

            if v1:
                c.extend(['%s%s%s' % (x, DELIMITER, self.all) for x in v1])

            if v2:
                c.extend(v2)

            for _c in c:

                if _data.has_key(_c):
                    _data[_c].append(r)

        del_keys = []

        for k in _data.keys():

            p = DELIMITER.join(k.split(DELIMITER)[0:-1])

            all_key = '%s%s%s' % (p, DELIMITER, self.all)

            other_keys = [x for x in _data.keys() if x.startswith('%s%s' % (p, DELIMITER))]

            if len(other_keys) > 1:
                if _data.has_key(all_key):
                    del_keys.append(all_key)

        for k in set(del_keys):
            del _data[k]

        for k in data.keys():

            for _k in _data.keys():

                if _k.startswith('%s%s' % (k, DELIMITER)):
                    data[k][_k] = _data[_k]

        return data

    def sort_key(self, x):
        return (x.Type, x.Title)

    def spreadsheet(self, data):

        heading = self.fields().headings

        wb = xlwt.Workbook()

        borders = xlwt.Borders()
        borders.left = borders.right = borders.top = borders.bottom = 1

        pattern = xlwt.Pattern()
        pattern.pattern_fore_colour = 22
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN

        heading_font = xlwt.Font()
        heading_font.name = 'Verdana'
        heading_font.bold = True

        heading_style = xlwt.XFStyle()
        heading_style.font = heading_font
        heading_style.borders = borders
        heading_style.pattern = pattern
        heading_style.alignment.wrap = True

        data_font = xlwt.Font()
        data_font.name = 'Verdana'

        data_style = xlwt.XFStyle()
        data_style.font = data_font
        data_style.borders = borders
        data_style.alignment.vert = 0

        wrap_data_style = deepcopy(data_style)
        wrap_data_style.alignment.wrap = True

        for (sheet, _data) in sorted(data.iteritems()):

            sheet_name = sheet.split(DELIMITER)[-1]
            sheet_name = sheet_name.replace('/', '-')
            ws = wb.add_sheet(sheet_name[0:31], cell_overwrite_ok=True) # Max string length 31

            row = 0

            for i in range(0, len(heading)):
                ws.write(row, i, heading[i], heading_style)

            if _data:
                for d in sorted(_data, key=lambda x: self.sort_key(x)):

                    v = self.fields(d, view=self, category=sheet).data

                    if v:

                        row = row + 1

                        for i in range(0, len(v)):

                            ws.write(row, i, v[i], data_style)

                        # Add category to sheet if we're that kind of workbook
                        if self.has_category:
                            ws.write(row, 1, sheet, data_style)

            # Hide first data columns
            for i in self.hidden_columns:
                ws.col(i).hidden = True

            # Set column widths
            widths = self.fields().widths

            for i in range(0,len(widths)):
                try:
                    w = widths[i]
                except IndexError:
                    pass
                else:
                    if w:
                        ws.col(i).width = 256*w

        outfile = StringIO.StringIO()

        try:
            wb.save(outfile)
        except:
            return None

        outfile.flush()

        return outfile

    @property
    def output_file(self):
        return self.zipfile

    # From http://www.kompato.com/post/43805938842/in-memory-zip-in-python
    @property
    def zipfile(self):

        data = self.data

        spreadsheets = []

        zip_data = StringIO.StringIO()

        zf = zipfile.ZipFile(zip_data, "a", zipfile.ZIP_DEFLATED, False)

        for (k, v) in data.iteritems():
            s = self.spreadsheet(v)

            if s:
                filename_in_zip = '%s.xls' % ploneify(k)

                # Write the file to the in-memory zip
                zf.writestr(filename_in_zip, s.getvalue())

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0

        zf.close()

        return zip_data.getvalue()

    def __call__(self):

        # No caching
        self.request.response.setHeader('Pragma', 'no-cache')
        self.request.response.setHeader('Cache-Control', 'private, no-cache, no-store')

        # Content Type
        self.request.response.setHeader('Content-Type', self.mime_type)

        # Filename
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % self.filename)

        # Return value
        return self.output_file

# Top X Products
class ExportTopProducts(ExportProducts):

    level = 2

    product_count = 50

    report = "top_%d_products" % product_count

    days = 60

    fields = TopProductResult

    def sort_key(self, x):
        return None

    @property
    @memoize
    def ga_sku_data(self):
        ga = GoogleAnalyticsBySKU()
        return ga.ga_sku_data(days=self.days)

    @property
    @memoize
    def category_sku_regex(self):
        v = CategorySKURegexView(self.context, self.request)
        data = v._getData()
        return dict([x[1:] for x in data])

    def regex_by_category(self, category):
        return self.category_sku_regex.get(category)

    def top_skus_by_category(self, category):
        # Get the regex that matches all SKUs in the category
        try:
            regex = re.compile(self.regex_by_category(category), re.I|re.M)

        except:
            # Couldn't find or compile a regex
            pass

        else:

            # Filter the data by the regex
            data = [(k,v) for (k,v) in self.ga_sku_data.iteritems() if regex.match(k)]

            # Sort by SKU
            data.sort(key=lambda x: x[-1], reverse=True)

            # Pull Top X
            if data:
                return [x[0] for x in data[0:self.product_count]]

        return []

    @property
    def data(self):
        _ = super(ExportTopProducts, self).data

        for (l1, v) in _.iteritems():

            for l2 in v.keys():

                # Get top X SKUs
                skus = self.top_skus_by_category(l2)

                # If we have a value for the skus
                if skus:

                    # Filter brains by top SKUs
                    v[l2] = [x for x in v[l2] if x.SKU in skus]

                    # Sort by position in SKU list. This doesn't work, figure out why!
                    v[l2].sort(key=lambda x: skus.index(x.SKU))

        return _

class ExportPeople(ExportProducts):

    level = 2

    report = 'people'

    fields = PersonResult

    @property
    def results(self):

        return self.portal_catalog.searchResults({
            'Type' : 'Person',
            'review_state' : ['published',],
        })

class ExportEvents(ExportProducts):

    level = 1

    hidden_columns = []

    mime_type = 'application/vnd.ms-excel'

    has_category = False

    fields = EventResult

    default_weeks = 3

    # Looks at the request for a 'weeks' parameter, and returns the integer.
    # If not is provided, uses the default
    @property
    def weeks(self):
        v = self.request.form.get('weeks', '')

        if v:

            try:
                return int(v)
            except (TypeError, ValueError):
                pass

        return self.default_weeks

    @property
    def filename(self):
        return "%s-%s.xls" % (self.datestamp, self.report)

    @property
    def end_date(self):
        return DateTime() + self.weeks*7.0

    @property
    def report(self):
        p = '%s-workshops-webinar-conferences'

        if self.county:
            return p % self.county.lower()

        return p % 'all'

    def sort_key(self, x):
        return (x.start, x.Title)

    def __init__(self, context, request, county=None):
        self.context = context
        self.request = request

        if county:
            self.county = county
        else:
            self.county = self.request.form.get('county', '')

        self.setHeaders()

    @property
    def counties(self):
        return getSurroundingCounties(self.county)

    @property
    def results(self):

        q = {
            'Type' : ['Workshop', 'Conference', 'Webinar', 'Cvent Event'],
            'review_state' : ['published',],
            'start' : {
                'range' : 'min',
                'query' : DateTime(),
            },
            'end' : {
                'range' : 'max',
                'query' : self.end_date,
            },
            'sort_on' : 'start',
        }

        results = self.portal_catalog.searchResults(q)

        for r in results:

            event_type = r.Type

            if r.Type in ['Cvent Event',]:

                p = r.getObject().aq_parent

                if IEventGroup.providedBy(p):
                    event_type = p.Type().replace(' Group', ''),

            if event_type in ['Webinar',] or \
               (r.County and set(r.County) & set(self.counties)) or \
               not self.county:
                yield r


    @property
    def data(self):
        return {'Upcoming Events' : [x for x in self.results]}

    @property
    def output_file(self):
        return self.spreadsheet(self.data).getvalue()