from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from zope import schema
from zope.interface import provider
from . import Container, IAtlasProduct

@provider(IFormFieldProvider)
class ICurriculum(IAtlasProduct):

    __doc__ = "Curriculum"

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

    continuing_education_cr_val = schema.TextLine(
        title=_(u"Continuing Education Credit Value"),
        description=_(u""),
        required=False,
    )


class Curriculum(Container):

    pass
