from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from zope import schema
from zope.component import adapter
from zope.interface import provider
from . import Container, IAtlasProduct

@provider(IFormFieldProvider)
class IPublication(IAtlasProduct):

    pdf_sample = NamedBlobFile(
        title=_(u"Sample PDF"),
        description=_(u""),
        required=False,
    )
    
    pdf = NamedBlobFile(
        title=_(u"Downloadable PDF"),
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
