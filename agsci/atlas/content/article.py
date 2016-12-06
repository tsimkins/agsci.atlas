from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import provider
from . import IArticleDexterityContent, IArticleDexterityContainedContent, Container, IAtlasProduct
from .behaviors import IPDFDownload

@provider(IFormFieldProvider)
class IArticle(IAtlasProduct, IArticleDexterityContent, IPDFDownload):

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['publication_reference_number', 'pdf_autogenerate',
                    'pdf_column_count', 'pdf_series', 'pdf_file'],
    )

    publication_reference_number = schema.TextLine(
        title=_(u"Publication Reference Number"),
        description=_(u"SKU of print publication associated with this article."),
        required=False,
    )

class IArticlePage(IArticleDexterityContainedContent):

    pass

class Article(Container):

    pass