from Missing import Value as MissingValue
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import safe_unicode
from DateTime import DateTime
from copy import deepcopy
from datetime import datetime
from plone.memoize.view import memoize
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.schema.interfaces import IVocabularyFactory

import StringIO
import re
import requests
import xlwt
import zipfile

from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DELIMITER, CMS_DOMAIN
from agsci.atlas.content.adapters import LocationAdapter, PDFDownload
from agsci.atlas.content.adapters.related_products import BaseRelatedProductsAdapter
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.content.structure import ICategoryLevel1
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.content.vocabulary.epas import UnitVocabulary, TeamVocabulary
from agsci.atlas.counties import getSurroundingCounties
from agsci.atlas.ga import GoogleAnalyticsBySKU
from agsci.atlas.utilities import execute_under_special_role, ploneify, format_value

from . import CategorySKURegexView
from .base import BaseView

class ProductResult(object):

    def format_value(self, x):
        return format_value(x, date_format=self.date_format)

    date_format = '%Y-%m-%d'

    def __init__(self, r=None, **kwargs):
        self.r = r
        self.view = kwargs.get('view', None)
        self.category = kwargs.get('category', None)

    @property
    def context(self):
        return getSite()

    def magento_url(self, _):
        if _.MagentoURL:
            return 'https://extension.psu.edu/%s' % _.MagentoURL

        return ''

    @property
    def widths(self):
        return [
            None, # UID
            None, # Category
            50, # Unit(s)
            50, # Team(s)
            20, # Product Type
            75, # Product Name
            15, # SKU
            100, # Description
            15, # Language(s)
            75, # CMS URL
            50, # Magento URL
            15, # Author(s)
            15, # Review State
            15 # Published Date
        ]

    @property
    def headings(self):
        return [
            "UID",
            "Category",
            "Unit(s)",
            "Team(s)",
            "Product Type",
            "Product Name",
            "SKU",
            "Description",
            "Language(s)",
            "CMS URL",
            "Magento URL",
            "Author(s)",
            "Review State",
            "Published Date",
        ]

    def toLocalizedTime(self, *args, **kwargs):
        return self.context.restrictedTraverse('@@plone').toLocalizedTime(*args, **kwargs)

    @property
    def data(self):
        return [
            self.format_value(x) for x in
            [
                self.r.UID,
                '',
                self.r.EPASUnit,
                self.r.EPASTeam,
                self.r.Type,
                self.r.Title,
                self.r.SKU,
                self.r.Description,
                getattr(self.r.getObject(), 'atlas_language', ''),
                self.r.getURL(),
                self.magento_url(self.r),
                self.r.Authors,
                self.r.review_state,
                self.r.effective,
            ]
        ]

# Result for the articles where we're trying to reconcile the published date
class ArticleResult(ProductResult):

    date_format = '%Y-%m-%d'

    @property
    def widths(self):
        return [
            None, None, 35, 20, 75, 100, 100, 11, 11, 11, 11
        ]

    @property
    def headings(self):
        return [
            "UID",
            "Category L1",
            "Category L2",
            "Type",
            "Title",
            "Description",
            "URL",
            "Old Extension Best Guess",
            "CMS Best Guess",
            "CMS Published Date",
            "PDF Copyright Year",
        ]

    @property
    def data(self):

        old_modified_date = self.view.get_old_extension_modified_date(self.r)
        category_l2 = self.view.get_category(self.r, 2)

        return [
            self.format_value(x) for x in
            [
                self.r.UID,
                '',
                category_l2,
                self.r.Type,
                self.r.Title,
                self.r.Description,
                self.r.getURL(),
                old_modified_date,
                self.r.content_owner_modified,
                self.r.effective,
                self.r.pdf_updated_year,
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
            self.format_value(x) for x in
            [
                self.r.UID,
                '',
                self.r.Type,
                self.r.Title,
                self.r.Description,
                self.r.getURL(),
                self.is_featured,
                self.is_educational_driver,
                self.view.ga_data.get(self.r.SKU, 0)
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
            self.format_value(x) for x in
            [
                self.r.UID,
                '',
                self.r.Title,
                self.r.getId,
                self.r.Classifications,
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

        return self.format_value(v)

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
                self.format_value(x) for x in
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

# Export all active products
class ExportProducts(BaseView):

    level = 3

    all = "All"

    mime_type = 'application/zip'

    report = "products"

    fields = ProductResult

    hidden_columns = [0,1]

    has_category = True

    review_state = ACTIVE_REVIEW_STATES

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
        q = {
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'IsChildProduct' : False,
        }

        if self.review_state:
            q['review_state'] = self.review_state

        return self.portal_catalog.searchResults(q)

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
    def l1(self):
        return 'CategoryLevel%d' % (self.level - 1)

    @property
    def l2(self):
        return 'CategoryLevel%d' % self.level

    @property
    def data_structures(self):

        return (
            dict([(x, {}) for x in self._terms(self.level - 1)]),
            dict([(x, []) for x in self.terms])
        )

    @property
    def data(self):

        (data, _data) = self.data_structures

        results = self.results

        for r in results:
            l1 = self.l1
            l2 = self.l2

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

# Export all products
class ExportAllProducts(ExportProducts):

    review_state = None

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
    def ga_data(self):
        ga = GoogleAnalyticsBySKU(days=self.days)
        return ga()

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
            data = [(k,v) for (k,v) in self.ga_data.iteritems() if regex.match(k)]

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

# Imported Articles: To set publishing date
class ExportArticlePublishedDate(ExportProducts):
    report = "imported_articles"

    fields = ArticleResult

    def __init__(self, context, request, county=None):
        self.context = context
        self.request = request

        self.old_extension_dates = self.download_old_extension_dates()

    def download_old_extension_dates(self):
        url = 'http://%s/magento/old-extension-best-guess.json' % CMS_DOMAIN
        return requests.get(url).json()

    def get_old_extension_modified_date(self, r):

        dates = [self.old_extension_dates.get(x, None) for x in r.OriginalPloneIds]

        dates = [x for x in dates if x]

        if dates:
            return DateTime(dates[0])

    @property
    def results(self):

        original_plone_ids = self.portal_catalog.uniqueValuesFor('OriginalPloneIds')
        original_plone_ids = [x for x in original_plone_ids if x]

        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'review_state' : ACTIVE_REVIEW_STATES,
            'Type' : 'Article',
            'OriginalPloneIds' : original_plone_ids,
        })

    def get_category(self, r, level=1):
        o = r.getObject()

        mc = AtlasMetadataCalculator('CategoryLevel%d' % level)

        adapted = BaseRelatedProductsAdapter(o)
        parent_category = adapted.parent_category

        try:
            v = mc.getMetadataForObject(parent_category)
        except AttributeError:
            v = None

        if not v:
            v = 'N/A'

        return v

    @property
    def data(self):

        data = {}

        for r in self.results:

            _current = r.effective
            _original = self.get_old_extension_modified_date(r)

            if _original:

                if abs(_current - _original) > 1:

                    l1 = self.get_category(r, level=1)

                    if not data.has_key(l1):
                        data[l1] = {
                            l1 : []
                        }

                    data[l1][l1].append(r)
                    data[l1][l1].sort(key=lambda x: x.Title)

        return data

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

        counties = self.counties

        for r in results:

            event_type = r.Type

            if r.Type in ['Cvent Event',]:

                p = r.getObject().aq_parent

                if IEventGroup.providedBy(p):
                    event_type = p.Type().replace(' Group', '')

            if event_type in ['Webinar',] or \
               (r.County and set(r.County) & set(counties)) or \
               not self.county:
                yield r

    @property
    def data(self):
        return {'Upcoming Events' : [x for x in self.results]}

    def getSpreadsheet(self):
        return self.spreadsheet(self.data).getvalue()

    @property
    def output_file(self):
        return execute_under_special_role(['Authenticated'], self.getSpreadsheet)

class ExportProductsEPAS(ExportProducts):

    report = "products_epas"

    l1 = "EPASUnit"
    l2 = "EPASTeam"

    def getVocabularyForLevel(self, level):

        return {
            self.l1 : "agsci.atlas.EPASUnit",
            self.l2 : "agsci.atlas.EPASTeam",
        }.get(level, None)

    def _terms(self, level, hidden=True):

        vocab_name = self.getVocabularyForLevel(level)

        if vocab_name:

            vocab_factory = getUtility(IVocabularyFactory, vocab_name)
            vocab = vocab_factory(self.context)
            return [x.value for x in vocab]

        return []

    @property
    def terms(self):

        _ = self._terms(self.l2)

        if self.level > 1:
            _.extend(['%s%s%s' % (x, DELIMITER, self.all) for x in self._terms(self.l1)])

        return sorted(_)

    @property
    def data_structures(self):

        return (
            dict([(x, {}) for x in self._terms(self.l1)]),
            dict([(x, []) for x in self.terms])
        )