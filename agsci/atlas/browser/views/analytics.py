from datetime import datetime

from . import AtlasStructureView

from agsci.atlas import object_factory
from agsci.atlas.ga import GoogleAnalyticsTopProductsByCategory, GoogleAnalyticsByCategory
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator

class CategoryView(AtlasStructureView):

    months = 6

    def __init__(self, context, request):
        super(CategoryView, self).__init__(context, request)

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

    # Formats the data for the top products into a data structure
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
            _['data'].append(
                object_factory(
                    sku=k,
                    data=v,
                    item=results.get(k, None),
                    total=0,
                )
            )

            _['months'].extend(v.keys())

        _['months'] = self.fix_months(_['months'])

        for i in _['data']:
            i.total = sum([i.data.get(x, 0) for x in _['months']])

        _['data'] = sorted(_['data'], key=lambda x: x.total, reverse=True)

        return object_factory(**_)