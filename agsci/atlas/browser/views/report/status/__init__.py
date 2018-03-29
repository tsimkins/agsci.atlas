from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from collections import namedtuple
from plone.memoize.view import memoize
from urllib import urlencode
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

from agsci.atlas import object_factory
from agsci.atlas.browser.views.base import BaseView
from agsci.atlas.utilities import SitePeople

@implementer(IPublishTraverse)
class AtlasContentStatusView(BaseView):

    review_state = []

    app_title = "Content Review"

    views = [
        ('view', 'All'),
        ('atlas_status_summary', 'Summary'),
        ('atlas_private', 'Private'),
        ('atlas_web_team_review', 'Web Team Review'),
        ('atlas_feedback_review', 'Owner Feedback'),
        ('atlas_published', 'Published'),
        ('atlas_expiring_soon', 'Expiring Soon'),
        ('atlas_expired', 'Expired'),
    ]

    review_state_data = {
        'published' : 'atlas_published',
        'published-inactive' : 'atlas_published',
        'private' : 'atlas_private',
        'pending' : 'atlas_web_team_review',
        'requires_feedback' : 'atlas_feedback_review',
        'expiring_soon' : 'atlas_expiring_soon',
        'expired' : 'atlas_expired',
    }

    nav_items = [ x[0] for x in views ]

    @property
    def portal_membership(self):
        return getToolByName(self.context, 'portal_membership')

    def getCurrentUser(self):
        user = self.portal_membership.getAuthenticatedMember()

        if user:
            return user.getId()

        return ''

    @property
    def portal_workflow(self):
        return getToolByName(self.context, 'portal_workflow')

    def getReviewStateClass(self, brain=None):
        if brain:
            if len(self.review_state) > 1:
                return 'state-%s' % brain.review_state

        return ''

    def getNavigationItemData(self, view_name):

        if view_name in ('view'):
            url = self.context.absolute_url()
        else:

            qs = self.getQueryString()

            if qs:
                url = '%s/@@%s?%s' % (self.context.absolute_url(), view_name, qs)
            else:
                url = '%s/@@%s' % (self.context.absolute_url(), view_name)

        return (url, self.getViewTitle(view_name), (self.__name__ == view_name), view_name)

    def navigation_items(self):
        return [self.getNavigationItemData(x) for x in self.nav_items]

    def getBaseProductQuery(self):
        return {'object_provides' : 'agsci.atlas.content.IAtlasProduct'}

    def getProductTypeQuery(self):

        _type = self.getSelectedProductType()

        if _type:

            return {'Type' : _type}

        return {}

    @property
    def filter_sets(self):
        from agsci.atlas.browser.views import FiltersView
        return FiltersView(self.context, self.request).filter_sets

    @property
    def filter_fields(self):
        return [x.field for x in self.filter_sets]

    def getFilterQuery(self):
        q = {}

        for i in self.filter_fields:
            v = self.request.form.get(i, [])

            if v:
                q[i] = v

        return q

    def attribute_filters(self):
        filter_sets = self.filter_sets

        _ = []

        for (k, v) in self.getFilterQuery().iteritems():
            for fs in filter_sets:
                if fs.field == k:
                    _.append(object_factory(title=fs.title, value=v))

        return sorted(_, key=lambda x: (x.title, x.value))

    def getURLParams(self, **kwargs):

        params = dict(self.request.form)

        params.update(kwargs)

        for (k,v) in dict(params).iteritems():
            if not v:
                del params[k]

        return params

    def getURLParamList(self):
        for (k,v) in self.getURLParams().iteritems():
            yield (k,v)

    def getQueryString(self, **kwargs):

        return urlencode(self.getURLParams(**kwargs))

    def getSelectedProductType(self):

        return self.request.form.get('Type', None)

    def getProductTypes(self):

        query = self.getProductQuery()

        if query.has_key('Type'):
            del query['Type']

        results = self.portal_catalog.searchResults(query)

        types = list(set([x.Type for x in results]))

        types.sort()

        return types

    def getSortFields(self):

        sort_options = namedtuple('SortOptions', 'label value')

        return [
             sort_options(**{ 'value' : 'sortable_title', 'label' : 'Title'}),
             sort_options(**{ 'value' : 'effective', 'label' : 'Published'}),
             sort_options(**{ 'value' : 'created', 'label' : 'Created'}),
        ]

    def getSortField(self):

        return self.request.form.get('sort_on', 'sortable_title')

    def getSortFieldQuery(self):

        sort_on = self.getSortField()

        q = { 'sort_on' : sort_on }

        if sort_on in ['created', 'effective']:
            q['sort_order'] = 'descending'

        return q

    @property
    def view_titles(self):
        return dict(self.views)

    def getViewTitle(self, view_name=None):
        if not view_name:
            view_name = self.__name__

        return self.view_titles.get(view_name, 'N/A')

    def getPOSTURL(self):
        view_name = self.__name__

        if view_name in ['view', '@@view']:
            return self.context.absolute_url()

        return '@@%s' % view_name

    @property
    def title(self):
        return '%s: %s' % (self.app_title, self.getViewTitle())

    def publishTraverse(self, request, name):

        if name:
            self.Owners = name

        return self

    @memoize
    def getSelectedOwner(self):

        user_id = getattr(self, 'Owners', self.request.form.get('Owners', None))

        if user_id:

            return user_id

        return None

    # Given either a brain or a string, get the user name from the user id
    @memoize
    def getUserName(self, v):

        user_id = ''

        if isinstance(v, AbstractCatalogBrain):
            owners = v.Owners

            if owners:
                user_id = owners[0]

        else:
            user_id = v

        user_name = self.getAllUsers().get(user_id, None)

        if user_name:
            return "%s (%s)" % (user_name, user_id)

        return user_id

    @memoize
    def getAllUsers(self):
        results = self.portal_catalog.searchResults({'Type' : 'Person'})

        return dict(map(lambda x: (x.getId, x.Title), results))

    def getReviewStateQuery(self):

        if self.review_state:
            return {'review_state' : self.review_state}

        return {}

    def getOwnersQuery(self):

        user_id = self.getSelectedOwner()

        if user_id:
            return {'Owners' : user_id}

        return {}

    def getStructureQuery(self):

        try:
            return self.context.getQueryForType()
        except:
            return {}

    def getChildProductQuery(self):
        return {}

    def getProductQuery(self):

        query = self.getBaseProductQuery()

        for q in [
                    self.getProductTypeQuery(),
                    self.getReviewStateQuery(),
                    self.getOwnersQuery(),
                    self.getStructureQuery(),
                    self.getChildProductQuery(),
                    self.getSortFieldQuery(),
                    self.getFilterQuery(),
                    ]:
            if q:
                query.update(q)


        return query

    @memoize
    def getResults(self, **contentFilter):
        query = self.getProductQuery()
        query.update(contentFilter)
        return self.portal_catalog.searchResults(query)

    @memoize
    def getValidPeople(self):

        sp = SitePeople()
        return sp.getValidPeople()

    @memoize
    def getValidPeopleIds(self):

        return map(lambda x: x.getId, self.getValidPeople())

    @memoize
    def getInvalidOwnerIds(self):

        all_owners = set(self.portal_catalog.uniqueValuesFor('Owners'))
        valid_owners = set(self.getValidPeopleIds())

        return list(all_owners - valid_owners)

    @memoize
    def getValidPeopleData(self):

        return dict(map(lambda x: (x.getId, x.Title), self.getValidPeople()))

    @memoize
    def getPersonNameById(self, person_id=None):

        return self.getValidPeopleData().get(person_id, 'Invalid User')

    def getOwners(self):
        owners = []

        for i in self.getResults():

            if i.Owners:
                owners.extend(i.Owners)

        owners = list(set(owners))

        owners.sort(key=lambda x: self.getUserName(x))

        return owners

    def show_image(self):
        return True

    @property
    def getTileColumns(self):
        if IPloneSiteRoot.providedBy(self.context):
            return '4'

        return '3'

    @property
    def hasTiledContents(self):
        return True

    def sku_regex(self, folderContents=[]):

        skus = sorted([x.SKU for x in folderContents if x.SKU])
        return '^(%s)$' % ("|".join(skus))


class AtlasPublishedView(AtlasContentStatusView):

    review_state = ["published", ]

class AtlasPrivateView(AtlasContentStatusView):

    review_state = ["private", ]

class AtlasWebTeamReviewView(AtlasContentStatusView):

    review_state = ['pending',]

class AtlasOwnerFeedbackView(AtlasContentStatusView):

    review_state = ['requires_feedback',]

class AtlasExpiringSoonView(AtlasContentStatusView):

    review_state = ['expiring_soon',]

class AtlasExpiredView(AtlasContentStatusView):

    review_state = ['expired',]

# Summary of all Content
class AtlasStatusSummary(AtlasContentStatusView):

    @property
    def review_state(self):
        return self.review_state_data.keys()

    # Report of products by state
    def getProductStateReport(self):

        data = []

        for r in self.getResults():

            review_state = r.review_state
            product_type = r.Type
            view_id = self.review_state_data.get(review_state, None)
            data.append((product_type, view_id))

        rv = []

        for i in set(data):
            _rv = list(i)
            _rv.append(data.count(i))
            rv.append(_rv)

        rv.sort(key=lambda x: self.getNavPosition(x[1]))
        rv.sort(key=lambda x:x[0])

        return rv

    # Report of products
    def getProductReport(self):

        data = []

        for r in self.getResults():

            product_type = r.Type
            data.append((product_type,))

        rv = []

        for i in set(data):
            _rv = list(i)
            _rv.append(data.count(i))
            rv.append(_rv)

        rv.sort(key=lambda x:x[0])

        return rv


    def getReviewStateReport(self):

        data = {}

        for r in self.getResults():
            review_state = r.review_state
            view_id = self.review_state_data.get(review_state, 'N/A')

            if not data.has_key(view_id):
                data[view_id] = []

            data[view_id].append(r)

        return data


    def getReviewStateByOwnerReport(self):

        data = {}

        for r in self.getResults():
            review_state = r.review_state
            view_id = self.review_state_data.get(review_state, 'N/A')

            owner = 'invalid_user'

            if r.Owners:
                _owner = r.Owners[0]
                if _owner in self.getValidPeopleIds():
                    owner = _owner

            if not data.has_key(view_id):
                data[view_id] = {}

            if not data[view_id].has_key(owner):
                data[view_id][owner] = []

            data[view_id][owner].append(r)

        return data


    @property
    def title(self):
        return '%s: %s' % (self.app_title, 'Summary')

    def getNavPosition(self, item):
        nav = self.nav_items

        if item in nav:
            return nav.index(item)

        return 99999

    def getSortedViews(self, v):
        return sorted(v, key=lambda x: self.getNavPosition(x))