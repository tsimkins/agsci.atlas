from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from plone.app.event.ical.exporter import EventsICal as _EventsICal
from plone.app.event.ical.exporter import ICalendarEventComponent as _ICalendarEventComponent
from plone.app.event.ical.exporter import construct_icalendar
from plone.event.interfaces import IICalendar, IICalendarEventComponent
from zope.interface import implementer

from agsci.atlas.content.vocabulary.calculator import AtlasMetadataCalculator
from agsci.atlas.cron.jobs.magento import MagentoJob

@implementer(IICalendarEventComponent)
class ICalendarEventComponent(_ICalendarEventComponent):

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
    _type = context.Type()
    mc = AtlasMetadataCalculator(_type)
    _value = mc.getMetadataForObject(context)
    portal_catalog = getToolByName(context, 'portal_catalog')
    results = portal_catalog.searchResults({
        'object_provides' : 'agsci.atlas.content.event.group.IEventGroup',
        'review_state' : 'published',
        _type : _value,
    })

    paths = [x.getPath() for x in results]

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

    return construct_icalendar(context, results)

class EventsICal(_EventsICal):

    def get_ical_string(self):
        cal = IICalendar(self.context)
        return cal.to_ical()
