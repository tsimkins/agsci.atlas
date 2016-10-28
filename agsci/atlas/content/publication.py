from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from zope import schema
from zope.component import adapter
from zope.interface import provider
from StringIO import StringIO
from . import Container, IAtlasProduct

try:
    from pyPdf import PdfFileReader
except ImportError:
    def PdfFileReader(*args, **kwargs):
        return None

@provider(IFormFieldProvider)
class IPublication(IAtlasProduct):

    __doc__ = "Publication"

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
        description=_(u"Manually set page count."),
        required=False,
    )


class Publication(Container):

    # If the page count is not manually set PDF is attached, automagically grab the page count for the API
    def getPageCount(self):
    
        # Get the hardcoded page count, and return if it's there
        page_count = getattr(self, 'pages_count', None)

        if page_count:
            return page_count

        # Otherwise, grab the page count from the attached PDF.
        elif self.pdf:
        
            if self.pdf.data and self.pdf.contentType == 'application/pdf':
                try:
                    pdf_data = StringIO(self.pdf.data)
                    pdf = PdfFileReader(pdf_data)
                    return pdf.getNumPages()
                except:
                    pass

        return