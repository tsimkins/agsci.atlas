from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.app.event.ical.exporter import EventsICal as _EventsICal
from plone.app.event.ical.exporter import ICalendarEventComponent as _ICalendarEventComponent
from plone.app.event.ical.exporter import construct_icalendar
from plone.event.interfaces import IICalendar, IICalendarEventComponent
from zope.interface import implementer
from zope.globalrequest import getRequest

from agsci.atlas.content.structure import IAtlasStructure
from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.cron.jobs.magento import MagentoJob
from agsci.atlas.constants import DELIMITER
from agsci.atlas.utilities import execute_under_special_role, ploneify

def get_request_filter():

    request_fields = [
        'EPASUnit',
        'EPASTeam',
        'EPASTopic',
    ]

    query = {}

    request = getRequest()

    for _ in request_fields:
        if _ in request and request.get(_):
            query[_] = request.get(_)

    return query

@implementer(IICalendarEventComponent)
class ICalendarEventComponent(_ICalendarEventComponent):

    def to_ical(self):

        ical_add = self.ical_add
        ical_add("dtstamp", self.dtstamp)
        ical_add("created", self.created)
        ical_add("last-modified", self.last_modified)
        ical_add("uid", self.uid)
        ical_add("url", self.url)
        ical_add("summary", self.summary)
        ical_add("description", self.description)
        ical_add("dtstart", self.dtstart)
        ical_add("dtend", self.dtend)
        ical_add("location", self.location)
        ical_add("categories", self.categories)

        return self.ical

    @property
    def categories(self):
        ret = [x.split(DELIMITER)[-1] for x in getattr(self.context.aq_parent, 'atlas_category_level_2', [])]

        if ret:
            return {"value": ret}

    @property
    def uid(self):
        uid = self.context.UID()
        sku = getattr(self.context.aq_base, 'sku', None)

        return {"value": ":".join([x for x in [uid, sku] if x])}

    @property
    def description(self):
        parent = self.context.aq_parent
        return {"value": parent.Description()}

    @property
    def location(self):
        location = ''

        city = getattr(self.context.aq_base, 'city', None)
        state = getattr(self.context.aq_base, 'state', None)

        if city and state:
            location = "%s, %s" % (city, state)

        return {"value": location}

    @property
    def url(self):

        url = "https://extension.psu.edu"

        mj = MagentoJob(self.context)

        parent = self.context.aq_parent

        uid = self.context.UID()
        p_uid = parent.UID()

        product = mj.by_plone_id(uid)
        p_product = mj.by_plone_id(p_uid)

        entity_id = mj.by_plone_id(uid).get('entity_id')
        magento_url = mj.by_plone_id(p_uid).get('magento_url')

        if entity_id and magento_url:
            url = 'https://extension.psu.edu/%s?entity=%s' % (magento_url, entity_id)

        return {"value": url}

@implementer(IICalendar)
def calendar_from_category(context):

    portal_catalog = getToolByName(context, 'portal_catalog')

    # All public event groups
    query = {
        'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
        'review_state' : 'published',
        'IsHiddenProduct' : False,
    }

    # Add a context filter
    if IAtlasStructure.providedBy(context):
        _type = context.Type()
        mc = AtlasMetadataCalculator(_type)
        _value = mc.getMetadataForObject(context)

        if _value:
            query[_type] = _value


    # Add a team filter
    if IPloneSiteRoot.providedBy(context):

        for (k,v) in get_request_filter().items():
            query[k] = v

    results = portal_catalog.searchResults(query)

    # Get paths from group products
    paths = [x.getPath() for x in results]

    # Get upcoming events in those paths of published, non-hidden group products

    results = portal_catalog.searchResults({
        'path' : paths,
        'object_provides' : 'agsci.atlas.content.event.IEvent',
        'review_state' : 'published',
        'end' : {
            'range' : 'min',
            'query' : DateTime(),
        },
        'sort_on' : 'start',
    })

    # Skip events that are longer than 31 days/1 month
    results = [x for x in results if (x.end - x.start).days <= 31]

    # Generate an ical from result set
    return construct_icalendar(context, results)

class EventsICal(_EventsICal):

    @property
    def filename(self):

        _id = self.context.getId()

        if IPloneSiteRoot.providedBy(self.context):

            _id = 'extension'

            query = get_request_filter()

            if query and query.values():
                _id = ploneify(sorted(query.values(), key=lambda x: len(x), reverse=True)[0])

        return _id

    def __call__(self):

        ical = execute_under_special_role(['Authenticated'], self.get_ical_string)

        name = f"{self.filename}.ics"

        self.request.response.setHeader("Content-Type", "text/calendar")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{name}"'
        )
        self.request.response.setHeader("Content-Length", len(ical))
        self.request.response.write(ical)
