from Products.CMFPlone.utils import safe_unicode
from copy import deepcopy
from datetime import datetime

import StringIO
import xlwt
import zipfile

from agsci.atlas.utilities import ploneify
from agsci.atlas.constants import ACTIVE_REVIEW_STATES, DELIMITER
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator

from .base import BaseView

class ProductResult(object):

    def __init__(self, r=None):
        self.r = r

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
                self.r.getURL(),
                '',
            ]
        ]

class ExportProducts(BaseView):

    level = 3
    all = "All"

    report = "products"

    fields = ProductResult

    @property
    def filename(self):
        return "%s-%s.zip" % (self.datestamp, self.report)

    @property
    def datestamp(self):
        return datetime.now().strftime('%Y%m%d_%H%M%S')

    @property
    def results(self):

        return self.portal_catalog.searchResults({
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'IsChildProduct' : False,
            'review_state' : ACTIVE_REVIEW_STATES,
        })

    def _terms(self, level):

        mc = AtlasMetadataCalculator('CategoryLevel%d' % level)
        return [x.value for x in mc.getTermsForType()]

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

    def spreadsheet(self, category, data):

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

            if _data:

                sheet_name = sheet.split(DELIMITER)[-1]
                sheet_name = sheet_name.replace('/', '-')
                ws = wb.add_sheet(sheet_name[0:31], cell_overwrite_ok=True) # Max string length 31

                row = 0

                for i in range(0, len(heading)):
                    ws.write(row, i, heading[i], heading_style)

                for d in sorted(_data, key=lambda x: self.sort_key(x)):

                    row = row + 1

                    v = self.fields(d).data

                    for i in range(0, len(v)):

                        ws.write(row, i, v[i], data_style)

                    # Add category to sheet
                    ws.write(row, 1, sheet, data_style)

                # Hide first two data columns
                ws.col(0).hidden = True
                ws.col(1).hidden = True

                # Set column widths
                widths = self.fields().widths

                for i in range(2,len(widths)):
                    ws.col(i).width = 256*widths[i]

        outfile = StringIO.StringIO()

        try:
            wb.save(outfile)
        except:
            return None

        outfile.flush()

        return outfile

    # From http://www.kompato.com/post/43805938842/in-memory-zip-in-python
    @property
    def zipfile(self):

        data = self.data

        spreadsheets = []

        zip_data = StringIO.StringIO()

        zf = zipfile.ZipFile(zip_data, "a", zipfile.ZIP_DEFLATED, False)

        for (k, v) in data.iteritems():
            s = self.spreadsheet(k, v)

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
        self.request.response.setHeader('Content-Type', 'application/zip')

        # Filename
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % self.filename)

        # Return value
        return self.zipfile

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
