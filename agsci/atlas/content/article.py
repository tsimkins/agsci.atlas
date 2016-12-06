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

    # Ensure that the SKU used for `publication_reference_number` is a valid SKU
    # of a publication
    @invariant
    def validatePublicationSKU(data):

        # Get the `publication_reference_number` value
        sku = getattr(data, 'publication_reference_number', None)

        # If the SKU of the printed pub was provided...
        if sku:

            # Normalize by stripping whitespace and uppercasing
            sku = sku.strip().upper()

            # Get the catalog
            portal_catalog = getToolByName(getSite(), 'portal_catalog')

            # dict of normalized SKU to actual SKU.
            # Note uppercase of index name
            existing_sku = dict([(x.strip().upper(), x) for x in portal_catalog.uniqueValuesFor('SKU') if x])

            # If the normalized SKU exists in the catalog
            if existing_sku.has_key(sku):

                # Query for a Publication with the actual SKU
                results = portal_catalog.searchResults({'SKU' : existing_sku[sku],
                                                        'Type' : 'Publication'})

                # If we find something, raise an error with that SKU and the path to the
                # existing object.
                if results:
                    return True

            # If a SKU was provided, and does not exist, or is not a valid
            # Publication SKU, raise an error.
            raise Invalid("SKU '%s' used for 'Publication Reference Number' is not a valid SKU of a Publication." % sku)


class IArticlePage(IArticleDexterityContainedContent):

    pass

class Article(Container):

    pass