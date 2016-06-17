from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from agsci.atlas.interfaces import IFilterSetMarker
from plone.dexterity.content import Container
from plone.autoform.interfaces import IFormFieldProvider

class IFilterSet(model.Schema):

    atlas_filters = schema.List(
        title=_(u"Filter(s)"),
        value_type=schema.TextLine(required=True),
        required=False,
    )

@implementer(IFilterSetMarker)
class FilterSet(Container):
    
    pass
    
