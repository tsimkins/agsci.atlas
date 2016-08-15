from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from zope import schema
from zope.component import adapter
from zope.interface import provider
from . import Container, IAtlasProduct
from .behaviors import IVideoBase

@provider(IFormFieldProvider)
class IOnlineCourse(IVideoBase, IAtlasProduct):

    # Should this just be the SKU?
    edx_id = schema.TextLine(
        title=_(u"edX Id"),
    )

@adapter(IOnlineCourse)
class OnlineCourse(Container):

    pass
