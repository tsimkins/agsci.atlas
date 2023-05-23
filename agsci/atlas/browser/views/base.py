from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from RestrictedPython.Utilities import same_type as _same_type
from RestrictedPython.Utilities import test as _test
from plone.event.interfaces import IEvent
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter, getUtility
from zope.interface import implementer, Interface
from zope.security import checkPermission

from agsci.atlas.content.behaviors.container import ITileFolder
from agsci.atlas.permissions import *
from agsci.atlas.utilities import truncate_text, generate_sku_regex
from agsci.leadimage.interfaces import ILeadImageMarker as ILeadImage

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

class IBaseView(Interface):
    pass


@implementer(IBaseView)
class BaseView(BrowserView):

    review_state_names = {
        'published' : 'Published',
        'published-inactive' : 'Published (Inactive)',
        'private' : 'Private',
        'pending' : 'Web Team Review',
        'requires_feedback' : 'Requires Feedback',
        'expiring_soon' : 'Expiring Soon',
        'expired' : 'Expired',
    }

    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.setHeaders()

    def setHeaders(self):

        # Prevent from being cached in proxy cache
        self.request.response.setHeader('Pragma', 'no-cache')
        self.request.response.setHeader('Cache-Control', 'private, no-cache, no-store')

    @property
    def show_date(self):
        return getattr(self.context, 'show_date', False)

    @property
    def show_description(self):
        return getattr(self.context, 'show_description', False)

    @property
    def show_image(self):
        return getattr(self.context, 'show_image', False)

    @property
    def show_read_more(self):
        return getattr(self.context, 'show_read_more', False)

    @property
    def _portal_state(self):
        return getMultiAdapter((self.context, self.request),
                                name=u'plone_portal_state')

    @property
    def _context_state(self):
        return getMultiAdapter((self.context, self.request),
                                name=u'plone_context_state')

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def wftool(self):
        return getToolByName(self.context, 'portal_workflow')

    @property
    def portal_membership(self):
        return getToolByName(self.context, 'portal_membership')

    @property
    def anonymous(self):
        return self._portal_state.anonymous()

    # Providing Restricted Python "test" method
    def test(self, *args):
        return _test(*args)

    # Providing Restricted Python "test" same_type
    def same_type(self, arg1, *args):
        return _same_type(arg1, *args)

    # Does this item have a leadimage?
    def getItemHasLeadImage(self, item):
        return getattr(item, 'hasLeadImage', False)

    def getItemLeadImage(self, item, css_class='leadimage', scale='leadimage_folder'):
        if self.getItemHasLeadImage(item):
            return ILeadImage(item.getObject()).tag(css_class=css_class, scale=scale)
        return ''

    @property
    def hasTiledContents(self):
        return ITileFolder.providedBy(self.context)

    def getLayout(self):
        if hasattr(self.context, 'getLayout') and self.context.getLayout():
            return self.context.getLayout()
        return ''

    @property
    def use_view_action(self):
        return getToolByName(self.context, 'portal_properties').get("site_properties").getProperty('typesUseViewActionInListings', ())

    def isPublication(self, item):
        return False

    def getItemURL(self, item):

        item_type = item.portal_type

        if hasattr(item, 'getURL'):
            item_url = item.getURL()
        else:
            item_url = item.absolute_url()

        # Logged out
        if self.anonymous:

            if item_type in ['Image',] or \
               (item_type in ['File',] and \
                    (self.isPublication(item) or not self.getFileType(item))):

                return item_url + '/view'

        if item_type in self.use_view_action:
            return item_url + '/view'

        return item_url

    def getIcon(self, item):

        if hasattr(item, 'getIcon'):

            if hasattr(item.getIcon, '__call__'):
                return item.getIcon()

            return item.getIcon

    def fileExtensionIcons(self):
        ms_data = ['xls', 'doc', 'ppt']

        data = {
            'xls' : u'Microsoft Excel',
            'ppt' : u'Microsoft PowerPoint',
            'publisher' : u'Microsoft Publisher',
            'doc' : u'Microsoft Word',
            'pdf' : u'PDF',
            'pdf_icon' : u'PDF',
            'text' : u'Plain Text',
            'txt' : u'Plain Text',
            'zip' : u'ZIP Archive',
        }

        for ms in ms_data:
            ms_type = data.get(ms, '')
            if ms_type:
                data['%sx' % ms] = ms_type

        return data

    def getFileType(self, item):

        icon = self.getIcon(item)

        if icon:
            icon = icon.split('.')[0]

        return self.fileExtensionIcons().get(icon, None)

    def getLinkType(self, url):

        if '.' in url:
            icon = url.strip().lower().split('.')[-1]

            return self.fileExtensionIcons().get(icon, None)

    def getItemSize(self, item):

        if hasattr(item, 'getObjSize'):

            if hasattr(item.getObjSize, '__call__'):
                return item.getObjSize()

            return item.getObjSize


    def getRemoteUrl(self, item):

        if hasattr(item, 'getRemoteUrl'):

            if hasattr(item.getRemoteUrl, '__call__'):
                return item.getRemoteUrl()

            return item.getRemoteUrl


    def getItemInfo(self, item):
        if item.portal_type in ['File',]:
            obj_size = self.getItemSize(item)
            file_type = self.getFileType(item)

            if file_type:
                if obj_size:
                    return u'%s, %s' % (file_type, obj_size)

                return u'%s' % file_type

        elif item.portal_type in ['Link',]:
            url = self.getRemoteUrl(item)
            return self.getLinkType(url)

    def getItemClass(self, item):

        # Default classes for all views
        item_class = ['listItem',]

        # If "Hide items excluded from navigation" is checked on the folder,
        # and this item is excluded, apply the 'excludeFromNav' class
        if getattr(self.context.aq_base, 'hide_exclude_from_nav', False) and getattr(item, 'exclude_from_nav'):
            item_class.append('excludeFromNav')

        # A class if we're showing leadimages
        if self.show_image:
            item_class.append('listItemLeadImage')

            if self.getItemHasLeadImage(item):
                item_class.append('listItemHasLeadImage')
            else:
                item_class.append('listItemMissingLeadImage')

        if self.hasTiledContents:
            item_class.append('list-item-columns-%s' % self.getTileColumns)

        return " ".join(item_class)

    def getItemDate(self, item):

        item_date = getattr(item, 'effective', getattr(item, 'created', None))

        if item_date:
            return item_date.strftime('%B %d, %Y')


    @property
    def getTileColumns(self):
        return '3'

    def isEvent(self, item):

        if getattr(item, 'getObject', False):
            item = item.getObject()

        return IEvent.providedBy(item)

    @memoize
    def getUserId(self):

        user_id = getattr(self, 'user_id', self.request.form.get('user_id', None))

        if user_id:
            return user_id

        user = self.portal_membership.getAuthenticatedMember()

        if user:
            return user.getId()

    def getFolderContents(self, **contentFilter):

        if self.context.Type() in ['Topic', 'Collection']:
            return self.context.queryCatalog(batch=False, **contentFilter)

        return self.context.getFolderContents(batch=False, **contentFilter)

    def getOwner(self, item=None):

        if item:

            owners = getattr(item, 'Owners', [])

            if owners:
                return owners[0]

    def getTruncatedDescription(self, item, max_chars=200, el='...'):

        description = item.Description

        if description:
            return truncate_text(description, max_chars=200, el='...')

        return ''

    def getIssues(self, item):
        issues = item.ContentIssues

        levels = ['High', 'Medium', 'Low', 'None']

        if issues:
            rv = []

            data = dict(zip(levels, issues))

            for k in levels:
                v = data.get(k)

                if isinstance(v, int) and v > 0:
                    rv.append(v*(' <span class="error-check-%s"></span> ' % k.lower()))
            if rv:
                return " ".join(rv)

            if not item.Type in ['Person',]:
                return '<span class="error-check-none"></span>'


    def getReviewStatusName(self, v):
        return self.review_state_names.get(v, v.replace('_', ' ').title())

    @property
    def registry(self):
        return getUtility(IRegistry)

    def generate_sku_regex(self, skus=[]):
        return generate_sku_regex(skus)

    @property
    def is_superuser(self):
        return checkPermission(ATLAS_SUPERUSER, self.context)

    @property
    def is_analytics(self):
        return checkPermission(ATLAS_ANALYTICS, self.context)

    @property
    def site(self):
        return getSite()
