from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventsContainerMarker
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

# Event container

class IEventsContainer(model.Schema):

    pass


@adapter(IEventsContainer)
@implementer(IEventsContainerMarker)
class EventsContainer(Container):

    def getContents(self, all=False, full_objects=False):
        portal_catalog = getToolByName(self, 'portal_catalog')
        
        # TODO: Make path dependent if no categories assigned,
        # otherwise, use categories in query
        
        query = {
                    'object_provides' : 'agsci.atlas.content.event.IEvent', 
                    'path' : '/'.join(self.getPhysicalPath())
                }

        if not all:
            query['end'] =  {'query' : DateTime(), 'range' : 'min'}

        results = portal_catalog.searchResults(query)

        if full_objects:
            return [x.getObject() for x in results]

        return results
