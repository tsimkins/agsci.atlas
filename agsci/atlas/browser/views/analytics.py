from Products.CMFPlone.utils import safe_unicode

from datetime import datetime

from . import AtlasStructureView, EPASSKUView

from agsci.atlas import object_factory
from agsci.atlas.constants import DELIMITER
from agsci.atlas.ga import GoogleAnalyticsTopProductsByCategory, \
                           GoogleAnalyticsByCategory, GoogleAnalyticsBySKU, \
                           GoogleAnalyticsByEPAS
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.utilities import ploneify

from urllib import urlencode

class AnalyticsBaseView(AtlasStructureView):

    months = 6

    product_data_limit = None

    tsv_headers = [
        'Product Type',
        'Product Name',
        'URL',
        'Review State',
        'Total',
    ]

    def __init__(self, context, request):
        super(AnalyticsBaseView, self).__init__(context, request)

        # Disable columns
        self.request.set('disable_plone.rightcolumn',1)
        self.request.set('disable_plone.leftcolumn',1)

    # Takes a list of YYYY-MM values, and removes the total and the current month.
    # Returns the latest self.months values.
    def fix_months(self, months):

        current_month = datetime.now().strftime('%Y-%m')

        months = sorted(set(months))

        if 'total' in months:
            months.remove('total')

        if current_month in months:
            months.remove(current_month)

        months = months[-1*(self.months):]

        months.reverse()

        return months

    # Updates the format to human-readable for a month key
    def fmt_month(self, _):
        try:
            return datetime.strptime(_, '%Y-%m').strftime('%B %Y')
        except:
            return _

    # Updates the format to human-readable for an integer
    def fmt_value(self, _):
        if isinstance(_, (int, float)):
            return "{:,}".format(_)
        return _

    # Formats the data for the top products into a data structure
    @property
    def product_data(self):

        _ = {
            'data' : [],
            'months' : [],
        }

        data = self.ga_product_data

        skus = data.keys()

        results = self.portal_catalog.searchResults({
            'SKU' : skus,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
        })

        results = dict([(x.SKU, x) for x in results if not x.IsChildProduct])

        for (k,v) in data.iteritems():

            item = results.get(k, None)

            if item:
                _['data'].append(
                    object_factory(
                        sku=k,
                        data=v,
                        item=item,
                        total=0,
                    )
                )

                _['months'].extend(v.keys())

        _['months'] = self.fix_months(_['months'])

        for i in _['data']:
            i.total = sum([i.data.get(x, 0) for x in _['months']])

        _['data'] = sorted(_['data'], key=lambda x: x.total, reverse=True)

        if self.product_data_limit:
            _['data'] = _['data'][:self.product_data_limit]

        return object_factory(**_)

    @property
    def tsv_filename(self):
        return datetime.now().strftime('%Y-%m-%d_%H%M%S')

    @property
    def tsv_data(self):

        rv = []

        product_data = self.product_data

        headers = list(self.tsv_headers)

        headers.extend([
            self.fmt_month(x) for x in product_data.months
        ])

        rv.append(headers)

        for i in product_data.data:
            r = i.item
            _ = [
                r.Type,
                r.Title,
                'https://extension.psu.edu/%s' % r.MagentoURL,
                r.review_state,
                self.fmt_value(i.total),
            ]
            _.extend([
                self.fmt_value(i.data.get(x, 0)) for x in product_data.months
            ])

            rv.append(_)

        rv = "\n".join(["\t".join([safe_unicode(y).encode('utf-8') for y in x]) for x in rv])

        return rv

    @property
    def tsv(self):
        self.request.response.setHeader('Content-Type', 'text/tab-separated-values')

        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename="%s-analytics.tsv"' % self.tsv_filename)

        return self.tsv_data

class PersonView(AnalyticsBaseView):

    # Get the Google Analytics data for the top products within a category
    @property
    def ga_product_data(self):

        results = self.portal_catalog.searchResults({
            'Authors' : self.username,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'sort_on' : 'sortable_title',
        })

        results = [x for x in results if x.SKU and not x.IsChildProduct]

        ga = GoogleAnalyticsBySKU()
        ga_data = ga.data

        rv = {}

        for r in results:
            for _ in ga_data:
                if _['sku'] == r.SKU:
                    _data = {}
                    for __ in _['values']:
                        _data[__['period']] = __['count']
                    rv[_['sku']] = _data
                    break

        return rv

    @property
    def username(self):
        return getattr(self.context, '', self.context.getId())

class PersonTSVView(PersonView):

    months = 12

    def __call__(self):
        return self.tsv

    @property
    def tsv_filename(self):
        return self.username

class CategoryView(AnalyticsBaseView):

    months = 6

    product_data_limit = 50

    # Returns the current category name and level
    @property
    def category_info(self):

        _type = self.context.Type()
        _level = int(_type[-1])

        mc = AtlasMetadataCalculator(_type)
        _category = mc.getMetadataForObject(self.context)

        return (_category, _level)

    # Get the Google Analytics data for the top products within a category
    @property
    def ga_product_data(self):

        (_category, _level) = self.category_info

        v = GoogleAnalyticsTopProductsByCategory(_category, _level)

        return v.ga_data()

    # Get the Google Analytics data for all products within a category
    @property
    def ga_category_data(self):

        (_category, _level) = self.category_info

        v = GoogleAnalyticsByCategory(_category, _level)

        return v.ga_data()

    # Formats the data for all products into a data structure
    @property
    def category_data(self):

        _ = {
            'data' : [],
            'months' : [],
        }

        data = self.ga_category_data

        for (k, v) in data.iteritems():
            _['data'].append(
                object_factory(
                    month=k,
                    **data[k]
                )
            )

            _['months'].append(k)

        _['months'] = self.fix_months(_['months'])

        _['data'] = sorted(_['data'], key=lambda x: x.month, reverse=True)

        _['data'] = [x for x in _['data'] if x.month in _['months']]

        return object_factory(**_)

class EPASView(CategoryView):

    months = 6

    title = u"EPAS Analytics"

    field_config = [
        {
            'name' : 'EPASUnit',
            'label' : 'Unit',
            'ga' : GoogleAnalyticsByEPAS,
        },
        {
            'name' : 'EPASTeam',
            'label' : 'Team',
            'ga' : GoogleAnalyticsByEPAS,
        },
        {
            'name' : 'EPASTopic',
            'label' : 'Topic',
            'ga' : None,
        },
    ]

    @property
    def fields(self):
        return [
            object_factory(**x) for x in self.field_config
        ]

    def __init__(self, context, request):

        super(EPASView, self).__init__(context, request)

        self.field = None

        for _ in reversed(self.fields):
            self.value = self.request.form.get(_.name, None)

            if self.value:
                self.field = _
                break

    def subtitle(self):

        if self.field:
            return "%s: %s" % (self.field.label, self.value)

    @property
    def sku_config(self):
        _ = EPASSKUView(self.context, self.request)
        return _._getData()

    # Filter the given values by a parent parameter
    def filter_values(self, parent, values):
        if parent:
            return [x for x in values if x.startswith('%s%s' % (parent, DELIMITER))]
        return values

    # Configuration of EPAS levels
    def get_epas_config(self, field):
        return self.sku_config.get(field.name, {})

    @property
    def epas_config(self):
        return self.get_epas_config(self.field)

    # Listing of values for EPAS levels, filtered by parent level if applicable.
    def get_epas_values(self, field):
        _ = sorted(self.get_epas_config(field).keys())
        return self.filter_values(self.value, _)

    @property
    def next_field(self):
        _ = self.fields

        if self.field:
            for idx in range(0,len(_)):
                if _[idx].name == self.field.name:
                    try:
                        return _[idx+1]
                    except IndexError:
                        return None

        return _[0]

    @property
    def config(self):

        field = self.field
        next_field = self.next_field

        kwargs = {
            'field' : self.field,
            'skus' : [],
            'next_field' : next_field,
            'children' : self.get_epas_values(next_field),
        }

        return object_factory(**kwargs)

    @property
    def skus(self):
        return self.epas_config.get(self.value, [])

    @property
    def show_category_data(self):
        return not not self.field.ga

    # Get the Google Analytics data for all products within a category
    @property
    def ga_category_data(self):
        ga = self.field.ga

        if ga:
            (_category, _level) = (self.value, self.field.label)

            v = ga(_category, _level)

            return v.ga_data()


    # Get the Google Analytics data for the top products within a category
    @property
    def ga_product_data(self):

        results = self.portal_catalog.searchResults({
            'SKU' : self.skus,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'sort_on' : 'sortable_title',
        })

        results = [x for x in results if x.SKU and not x.IsChildProduct]

        ga = GoogleAnalyticsBySKU()
        ga_data = ga.data

        rv = {}

        for r in results:
            for _ in ga_data:
                if _['sku'] == r.SKU:
                    _data = {}
                    for __ in _['values']:
                        _data[__['period']] = __['count']
                    rv[_['sku']] = _data
                    break

        return rv

    @property
    def tsv_url(self):

        if self.value:
            return "%s/@@epas_analytics_tsv?%s" % (
                self.context.absolute_url(),
                urlencode({self.field.name : self.value})
            )

class EPASTSVView(EPASView):

    months = 12

    product_data_limit = None

    def __call__(self):
        return self.tsv

    @property
    def tsv_filename(self):
        return ploneify("-".join([self.field.label, self.value]))
