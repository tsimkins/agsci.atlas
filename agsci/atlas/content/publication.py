from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider
from . import Container

@provider(IFormFieldProvider)
class IPublication(model.Schema):

    file = NamedBlobFile(
        title=_(u"Sample File"),
        description=_(u""),
        required=False,
    )

    pages_count = schema.Int(
        title=_(u"Page Count"),
        description=_(u""),
        required=False,
    )

@adapter(IPublication)
class Publication(Container):

    pass