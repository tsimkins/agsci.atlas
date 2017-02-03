from .. import Event, ILocationEvent
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.permissions import *
from agsci.atlas.content.behaviors import IAtlasLocation
from plone.supermodel import model
from zope import schema
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider

@provider(IFormFieldProvider)
class ICventEvent(ILocationEvent):

    __doc__ = "Cvent Event"

    def getRestrictedFieldConfig():

        # Initialize display-only fields
        fields = ['cvent_id', 'cvent_url']

        # Transform list into kw dictionary and return
        return dict([(x, ATLAS_SUPERUSER) for x in fields])

    def getDisplayFieldConfig():

        # Initialize display fields with location names
        fields = IAtlasLocation.names()

        # Transform list into kw dictionary and return
        return dict([(x, 'display') for x in fields])

    # Set write permissions for form.
    form.write_permission(**getRestrictedFieldConfig())

    # Set display-only fields
    form.mode(**getDisplayFieldConfig())

    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=('cvent_id', 'cvent_url'),
        )

    atlas_event_type = schema.Choice(
        title=_(u"Event Type"),
        vocabulary="agsci.atlas.CventEventType",
        default=u"Workshop",
        required=True,
    )

    cvent_id = schema.TextLine(
            title=_(u"Cvent Event Id"),
            description=_(u""),
            required=False,
        )

    cvent_url = schema.TextLine(
            title=_(u"Cvent Event URL"),
            description=_(u""),
            required=False,
        )

class CventEvent(Event):
    pass
