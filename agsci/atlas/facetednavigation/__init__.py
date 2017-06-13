from Products.CMFCore.utils import getToolByName
from eea.facetednavigation.criteria.handler import Criteria as _Criteria
from eea.facetednavigation.criteria.interfaces import ICriteria
from eea.facetednavigation.widgets.storage import Criterion
from persistent.list import PersistentList
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.schema import getFieldNamesInOrder

from ..content.behaviors import IAtlasFilterSets

@implementer(ICriteria)
class Criteria(_Criteria):

    # Get the filtersets that are configured on all of the CategoryLevel3 items
    # under this object
    def getConfiguredFilterSets(self):

        portal_catalog = getToolByName(self.context, 'portal_catalog')
        path  = '/'.join(self.context.getPhysicalPath())

        results = portal_catalog.searchResults({'Type' : 'CategoryLevel3', 'path' : path})

        filtersets = []

        for r in results:
            o = r.getObject()
            v = getattr(o, 'atlas_filter_sets', [])
            if v:
                filtersets.extend(v)

        return list(set(filtersets))

    def getFilters(self):

        # Get intersection of configured filtersets and valid filtersets, in
        # order.
        configured_filtersets = [x for x in self.getConfiguredFilterSets()]

        schema_filtersets = getFieldNamesInOrder(IAtlasFilterSets)

        configured_schema_filtersets = [x for x in schema_filtersets if x in configured_filtersets]

        for key in configured_schema_filtersets:

            # Get the field object
            field = IAtlasFilterSets.getDescriptionFor(key)

            # Set the cid to the key, minus 'atlas', and replace underscores.
            cid = key
            cid = cid.replace('atlas_', '').replace('_', '')

            # Get the vocabulary name
            value_type = field.value_type
            vocabulary_name = value_type.vocabularyName

            # Title is the field title
            title = field.title

            yield Criterion(
                _cid_=cid,
                widget="checkbox",
                title=title,
                index=key,
                operator="or",
                operator_visible=False,
                vocabulary=vocabulary_name,
                position="left",
                section="default",
                hidden=False,
                count=True,
                catalog="",
                sortcountable=False,
                hidezerocount=False,
                maxitems=50,
                sortreversed=False,
            )

    @property
    def request(self):
        return getRequest()

    # Caching call for criteria on request, so we don't have to recalculate
    # each time.
    def _criteria(self):
        cache = IAnnotations(self.request)
        key = 'eea.facetednav.%s' % self.context.UID()

        if not cache.has_key(key):
            cache[key] = self.__criteria()

        return cache[key]

    def __criteria(self):

        criteria = [
            Criterion(
                _cid_='productstatus',
                widget="select",
                title="Product Status",
                index="review_state",
                vocabulary="agsci.atlas.ProductStatus",
                position="left",
                section="default",
                hidden=False,
                count=True,
                sortcountable=False,
                hidezerocount=True,
                sortreversed=False,
            ),
            Criterion(
                _cid_='sortby',
                widget="sorting",
                title="Sort By",
                vocabulary="agsci.atlas.SortOrder",
                position="left",
                section="default",
                hidden=False,
            ),
            Criterion(
                _cid_='owner',
                widget="select",
                title="Owner",
                index="Owners",
                vocabulary="agsci.atlas.People",
                catalog="",
                position="left",
                section="default",
                hidden=False,
                count=True,
                sortcountable=False,
                hidezerocount=True,
                sortreversed=False,
            ),
            Criterion(
                _cid_='producttype',
                widget="checkbox",
                title="Product Type",
                index="Type",
                operator="or",
                operator_visible=False,
                vocabulary="",
                catalog="portal_catalog",
                position="left",
                section="default",
                hidden=False,
                count=True,
                sortcountable=False,
                hidezerocount=True,
                maxitems=100,
                sortreversed=False,
            ),
            Criterion(
                widget="criteria",
                title="Current search",
                position="center",
                section="default",
                hidden=False,
            ),
        ]

        criteria.extend(self.getFilters())

        return PersistentList(criteria)

