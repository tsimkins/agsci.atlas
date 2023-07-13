from Products.CMFPlone.utils import safe_unicode

from datetime import datetime

from . import AtlasStructureView, EPASSKUView, PersonReviewQueueView

from agsci.atlas import object_factory
from agsci.atlas.constants import DELIMITER, REVIEW_PERIOD_YEARS
from agsci.atlas.ga import GoogleAnalyticsTopProductsByCategory, \
                           GoogleAnalyticsByCategory, GoogleAnalyticsBySKU, \
                           GoogleAnalyticsByEPAS, YouTubeAnalyticsData
from agsci.atlas.content.adapters import VideoSeriesDataAdapter
from agsci.atlas.content.video import IVideo, IVideoSeries
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.utilities import ploneify, format_value, SitePeople, get_csv

try:
    from urllib.parse import urlencode # Python 3
except ImportError:
    from urllib import urlencode # Python 2

from .export import ProductResult

class AnalyticsProductResult(ProductResult):

    headings = [
        'Product Type',
        'Product Name',
        'CMS URL',
        'Public URL',
        'SKU',
        "Owner(s)",
        "Author(s)",
        "Review State",
        "Published Date",
        "Expiration Date",
    ]

    @property
    def data(self):
        return [
            self.format_value(x) for x in
            [
                self.r.Type,
                self.r.Title,
                self.r.getURL(),
                'https://extension.psu.edu/%s' % self.r.MagentoURL,
                self.r.SKU,
                self.r.Owners,
                self.r.Authors,
                self.r.review_state,
                self.r.effective,
                self.expiration_date(self.r),
            ]
        ]

    # Pull names of authors
    def getPeopleNames(self, _):
        if _:
            names = [self.getPersonName(x) for x in _]
            names = [x for x in names if x]
            return names

    def getPersonName(self, _):
        sp = SitePeople(active=False)
        p = sp.getPersonById(_)
        if p:
            return p.Title

class EPASAnalyticsProductResult(AnalyticsProductResult):

    headings = [
        'Product Type',
        'Product Name',
        'SKU',
        'CMS URL',
        'Public URL',
        'Language(s)',
        'Review State',
        'Owner(s)',
        'Author(s)',
        'Published',
        'Expiration Date',
    ]

    @property
    def data(self):
        return [
            self.format_value(x) for x in
            [
                self.r.Type,
                self.r.Title,
                self.r.SKU,
                self.r.getURL(),
                'https://extension.psu.edu/%s' % self.r.MagentoURL,
                getattr(self.r.getObject(), 'atlas_language', ''),
                self.r.review_state,
                self.r.Owners,
                self.r.Authors,
                self.r.effective,
                self.expiration_date(self.r),
            ]
        ]

class EPASCSVAnalyticsProductResult(AnalyticsProductResult):

    headings = [
        'Unit(s)',
        'Team(s)',
        'Product Type',
        'Product Name',
        'SKU',
        'CMS URL',
        'Public URL',
        'Language(s)',
        'Review State',
        'Owner(s)',
        'Author(s)',
        'Published',
        'Expiration Date',
    ]

    @property
    def data(self):
        return [
            self.format_value(x) for x in
            [
                self.r.EPASUnit,
                self.r.EPASTeam,
                self.r.Type,
                self.r.Title,
                self.r.SKU,
                self.r.getURL(),
                'https://extension.psu.edu/%s' % self.r.MagentoURL,
                getattr(self.r.getObject(), 'atlas_language', ''),
                self.r.review_state,
                self.r.Owners,
                self.r.Authors,
                self.r.effective,
                self.expiration_date(self.r),
            ]
        ]

class CategoryEPASCSVProductResult(AnalyticsProductResult):

    headings = [
        'Category Level 1',
        'Category Level 2',
        'Unit(s)',
        'Team(s)',
        'Product Type',
        'Product Name',
        'Product Description',
        'SKU',
        'CMS URL',
        'Public URL',
        'Language(s)',
        'Review State',
        'Owner Id(s)',
        'Owner Name(s)',
        'Author Id(s)',
        'Author Name(s)',
        'Published',
        'Expiration Date',
    ]

    @property
    def data(self):

        return [
            self.format_value(x) for x in
            [
                self.r.CategoryLevel1,
                self.r.CategoryLevel2,
                self.r.EPASUnit,
                self.r.EPASTeam,
                self.r.Type,
                self.r.Title,
                self.r.Description,
                self.r.SKU,
                self.r.getURL(),
                'https://extension.psu.edu/%s' % self.r.MagentoURL,
                getattr(self.r.getObject(), 'atlas_language', ''),
                self.r.review_state,
                self.r.Owners,
                self.getPeopleNames(self.r.Owners),
                self.r.Authors,
                self.getPeopleNames(self.r.Authors),
                self.r.effective,
                self.expiration_date(self.r),
            ]
        ]

class AnalyticsBaseView(AtlasStructureView):

    __months__ = 6

    @property
    def months(self):
        _ = self.request.get('months')

        if _ and isinstance(_, (str, )) and _.isdigit():
            return int(_)

        return self.__months__

    product_data_limit = None

    fields = AnalyticsProductResult

    def format_value(self, x):
        return format_value(x)

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

    # Formats the data for the top products into a data structure
    @property
    def product_data(self):

        _ = {
            'data' : [],
            'months' : [],
        }

        data = self.ga_product_data

        skus = list(data.keys())

        results = self.portal_catalog.searchResults({
            'SKU' : skus,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
        })

        results = dict([(x.SKU, x) for x in results if not x.IsChildProduct])

        for (k,v) in data.items():

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
    def csv_filename(self):
        return datetime.now().strftime('%Y-%m-%d_%H%M%S')

    def getCSV(self):

        product_data = self.product_data

        headers = list(self.fields.headings)

        headers.append('Total')

        headers.extend([
            self.fmt_month(x) for x in product_data.months
        ])

        data = []

        for i in product_data.data:
            r = i.item

            _ = self.fields(r).data

            _.append(self.format_value(i.total))

            _.extend([
                self.format_value(i.data.get(x, 0)) for x in product_data.months
            ])

            data.append(_)

        return get_csv(
            headers=headers,
            data=data
        )

    @property
    def csv(self):
        self.request.response.setHeader('Content-Type', 'text/csv')

        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename="%s-analytics.csv"' % self.csv_filename)

        return self.getCSV()

class PersonView(AnalyticsBaseView):

    @property
    def search_criteria(self):
        return {
            'Authors' : self.username,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'sort_on' : 'sortable_title',
        }

    # Get the Google Analytics data for the top products within a category
    @property
    def ga_product_data(self):

        results = self.portal_catalog.searchResults(self.search_criteria)

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

class PersonCSVView(PersonView):

    __months__ = 12

    def __call__(self):
        return self.csv

    @property
    def csv_filename(self):
        return self.username

class PersonOwnerCSVView(PersonCSVView):

    @property
    def search_criteria(self):
        return {
            'Owners' : self.username,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'sort_on' : 'sortable_title',
        }

class CategoryView(AnalyticsBaseView):

    __months__ = 6

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

        v = GoogleAnalyticsTopProductsByCategory(category=_category, level=_level)

        return v()

    # Get the Google Analytics data for all products within a category
    @property
    def ga_category_data(self):

        (_category, _level) = self.category_info

        v = GoogleAnalyticsByCategory(category=_category, level=_level)

        return v()

    # Formats the data for all products into a data structure
    @property
    def category_data(self):

        _ = {
            'data' : [],
            'months' : [],
        }

        data = self.ga_category_data

        for (k, v) in data.items():
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

class CategoryCSVView(CategoryView):

    fields = EPASAnalyticsProductResult

    __months__ = 12

    product_data_limit = None

    def __call__(self):
        return self.csv

    @property
    def csv_filename(self):
        return self.context.getId()

    @property
    def ga_product_data(self):

        (_category, _level) = self.category_info

        results = self.portal_catalog.searchResults({
            'CategoryLevel%d' % _level : _category,
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

class EPASView(CategoryView):

    __months__ = 6

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
    def epas_fields(self):
        return [
            object_factory(**x) for x in self.field_config
        ]

    def __init__(self, context, request):

        super(EPASView, self).__init__(context, request)

        self.field = None
        self.value = None

        for _ in reversed(self.epas_fields):
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
        _ = self.epas_fields

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
        if self.value:
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

            v = ga(category=_category, level=_level)

            return v()


    # Get the Google Analytics data for the top products within a category
    @property
    def ga_product_data(self):

        skus = self.skus

        q = {
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
            'sort_on' : 'sortable_title',
        }

        # Only filter by sku if skus are provided *or* we have a field defined.
        # This makes a "show all products" report works, without all of the products
        # showing for fields that have no products.
        if skus or self.field:
            q['SKU'] = skus

        results = self.portal_catalog.searchResults(q)

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
    def csv_url(self):

        if self.value:
            return "%s/@@epas_analytics_csv?%s" % (
                self.context.absolute_url(),
                urlencode({self.field.name : self.value})
            )

class TeamReviewQueueView(PersonReviewQueueView, EPASView):

    @property
    def view_filters(self):
        return {
            'SKU' : self.skus
        }

class EPASCSVView(EPASView):

    __months__ = 12

    product_data_limit = None

    fields = EPASCSVAnalyticsProductResult

    def __call__(self):
        return self.csv

    @property
    def csv_filename(self):
        if self.field and self.field.label and self.value:
            return ploneify("-".join([self.field.label, self.value]))
        return 'all-units'

class CategoryEPASCSVView(AnalyticsBaseView):

    __months__ = 12

    product_data_limit = None

    fields = CategoryEPASCSVProductResult

    def __call__(self):
        return self.csv

    # Get the Google Analytics data for the top products within a category
    @property
    def ga_product_data(self):

        results = self.portal_catalog.searchResults({
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
    def csv_filename(self):
        return 'category-epas'

class ProductView(AnalyticsBaseView):

    @property
    def sku(self):
        return getattr(self.context.aq_base, 'sku', None)

    def total(self, _):
        return sum([x.count for x in _ if x.count])

    def get_video_analytics(self, **kwargs):

        sku = kwargs.get('sku', None)

        if sku:

            _data = []

            ga = YouTubeAnalyticsData()
            ga_data = ga.data

            for _ in ga_data:

                if _['sku'] == sku:

                    for __ in _['values']:

                        __data = {}
                        __data.update(kwargs)
                        __data.update(__)

                        _data.append(object_factory(**__data))

                    _data.sort(key=lambda x:x.period, reverse=True)

                    return _data

        return []

    @property
    def is_video_series(self):
        return IVideoSeries.providedBy(self.context)

    @property
    def is_video(self):
        return IVideo.providedBy(self.context)

    @property
    def videos(self):
        if self.is_video_series:
            return VideoSeriesDataAdapter(self.context).getVideoBrains()

    @property
    def video_data(self):

        if self.is_video_series:

            videos = self.videos

            if videos:

                data = []

                for _ in videos:

                    data.extend(
                        self.get_video_analytics(
                            sku=_.SKU,
                            name=_.Title,
                            link=_.getURL(),
                        )
                    )

                data.sort(key=lambda x:x.period, reverse=True)

                return data

        elif self.is_video:
            return self.get_video_analytics(sku=self.sku)

        return []

    @property
    def product_data(self):

        results = self.portal_catalog.searchResults({
            'SKU' : self.sku,
            'object_provides' : 'agsci.atlas.content.IAtlasProduct',
        })

        results = [x for x in results if x.SKU and not x.IsChildProduct]

        if results:

            ga = GoogleAnalyticsBySKU()
            ga_data = ga.data

            for r in results:

                for _ in ga_data:

                    if _['sku'] == r.SKU:

                        _data = [
                            object_factory(**x) for x in _['values']
                        ]

                        _data.sort(key=lambda x:x.period, reverse=True)

                        return _data

        return []
