from Products.CMFPlone.utils import safe_unicode
from DateTime import DateTime
from copy import deepcopy
from datetime import datetime
from zope.component.hooks import getSite

import StringIO
import xlwt
import zipfile

from agsci.atlas.utilities import ploneify
from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DELIMITER
from agsci.atlas.content.adapters import LocationAdapter
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.counties import getSurroundingCounties

from .base import BaseView

class ProductResult(object):

    def __init__(self, r=None):
        self.r = r

    @property
    def context(self):
        return getSite()

    def scrub(self, x):
        return safe_unicode(" ".join(x.strip().split()))

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
            "Event Type",
            "Title",
            "Description",
            "Date/Time",
            "County",
            "Address",
            "Price",
            "URL",
            "Phone",
            "Email",
            "Registration Deadline",
        ]

    @property
    def widths(self):
        return [
            12, 50, 50, 52, 12, 78, 10, 50, 13, 26, 24
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

    @property
    def data(self):

        r = self.r
        o = r.getObject()
        p = o.aq_parent

        if IEventGroup.providedBy(p):

            return [
                self.scrub(x) for x in
                [
                    p.Type().replace(' Group', ''),
                    p.Title(),
                    p.Description(),
                    self.toLocalizedTime(r.start, end_time=r.end, long_format=True),
                    self.county(o),
                    self.address(o),
                    self.price(o),
                    self.magento_url(p),
                    '877-345-0691',
                    'ExtensionSupport@psu.edu',
                    self.registration_deadline(o),
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

                    row = row + 1

                    v = self.fields(d).data

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

    @property
    def filename(self):
        return "%s-%s.xls" % (self.datestamp, self.report)

    @property
    def end_date(self):
        return DateTime() + 6*30.5

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

        data = dict([(x, []) for x in self._terms(self.level, hidden=False)])

        results = self.results

        for r in results:
            l1 = 'atlas_category_level_1'

            p = r.getObject().aq_parent

            v1 = getattr(p, l1, [])

            if v1:

                for _c in v1:

                    if data.has_key(_c):
                        data[_c].append(r)

        return data

    @property
    def output_file(self):
        return self.spreadsheet(self.data).getvalue()