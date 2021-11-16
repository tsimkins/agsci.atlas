from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.interface import provider
from zope import schema

from . import IArticleDexterityContent, IArticleDexterityContainedContent, \
              Container, IAtlasProduct

from .behaviors import IPDFDownload

@provider(IFormFieldProvider)
class IArticle(IAtlasProduct, IArticleDexterityContent, IPDFDownload):

    __doc__ = 'Article'

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['pdf_autogenerate',
                    'pdf_column_count', 'pdf_series', 'pdf_file',
                    'pages_count',],
    )

    pages_count = schema.Int(
        title=_(u"Page Count"),
        description=_(u"Manually set page count for Publication."),
        required=False,
    )

class IArticlePage(IArticleDexterityContainedContent):

    # Internal
    model.fieldset(
            'settings',
            label=_(u'Settings'),
            fields=['show_title_as_heading',],
    )

    show_title_as_heading = schema.Bool(
        title=_(u"Show title as a heading."),
        description=_(u"Only if this is a multi-page article, and the heading doesn't match the article title."),
        required=False,
        default=True,
    )

class Article(Container):

    pass