from .. import Event, ILocationEvent
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content.behaviors import IAtlasLocation
from plone.supermodel import model
from zope import schema
from plone.autoform import directives as form

# Define read permission
write_permission = 'agsci.atlas.super'

class ICventEvent(ILocationEvent):

    def getReadOnlyFieldConfig(v):
    
        # Initialize read-only fields with location names
        read_only_fields = list(IAtlasLocation.names())
        
        # Append Cvent fields to read_only_fields
        read_only_fields.extend(['cvent_id', 'cvent_url'])
        
        # Transform list into kw dictionary and return
        return dict([(x, v) for x in read_only_fields])
        
    # Set write permissions for form.
    form.write_permission(**getReadOnlyFieldConfig(write_permission))

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
