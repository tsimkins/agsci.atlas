from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.component import adapter
from zope.interface import provider, implementer
from ..interfaces import IArticleMarker
from . import IArticleDexterityContent, IArticleDexterityContainedContent, Container, IAtlasProduct
from .behaviors import IPDFDownload

@provider(IFormFieldProvider)
class IArticle(IAtlasProduct, IArticleDexterityContent, IPDFDownload):

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['pdf_autogenerate', 'pdf_column_count', 'pdf_series', 'pdf_file'],
    )


class IArticlePage(IArticleDexterityContainedContent):

    pass

@adapter(IArticle)
@implementer(IArticleMarker)
class Article(Container):

    page_types = [u'Video', u'Article Page', u'Slideshow',]