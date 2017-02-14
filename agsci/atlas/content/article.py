from Products.CMFCore.utils import getToolByName
from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component.hooks import getSite
from zope.interface import provider, invariant, Invalid
from . import IArticleDexterityContent, IArticleDexterityContainedContent, Container, IAtlasProduct
from .behaviors import IPDFDownload

@provider(IFormFieldProvider)
class IArticle(IAtlasProduct, IArticleDexterityContent, IPDFDownload):

    __doc__ = 'Article'

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=['pdf_autogenerate',
                    'pdf_column_count', 'pdf_series', 'pdf_file'],
    )

class IArticlePage(IArticleDexterityContainedContent):

    pass

class Article(Container):

    pass