from BeautifulSoup import BeautifulSoup, NavigableString, Tag
from DateTime import DateTime

from PIL import Image as PILImage

from Products.CMFCore.utils import getToolByName

from StringIO import StringIO
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Image, BaseDocTemplate, Frame, PageTemplate, FrameBreak
from reportlab.platypus.figures import FlexFigure
from reportlab.platypus.figures import ImageFigure as ImageFigureBase
from reportlab.platypus.flowables import HRFlowable, KeepTogether, ImageAndFlowables
from reportlab.platypus.tables import Table, TableStyle
from reportlab.rl_config import _FUZZ

from urlparse import urljoin
from uuid import uuid1
from uuid import uuid4

from agsci.atlas.utilities import increaseHeadingLevel

from agsci.atlas.interfaces import IArticleMarker

import re

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite


# Image with a caption below it
class ImageFigure(ImageFigureBase, Image):

    def __init__(self, img_data, caption, width, height, background=None, align='right', max_image_width=None, column_count=1):
        self.img = PILImage.open(img_data)
        w, h = self.img.size

        if max_image_width > w:
            scaleFactor = max_image_width/w
        else:
            scaleFactor = width/w

        FlexFigure.__init__(self, w*scaleFactor, h*scaleFactor, caption, background)
        self.border=0
        self.captionFont='Helvetica'
        self.captionTextColor=HexColor('#717171')
        self.captionSize=9
        self.scaleFactor = self._scaleFactor = scaleFactor
        self.vAlign = 'TOP'
        self.hAlign = 'LEFT'
        self.column_count = column_count

    def drawFigure(self):
        (w,h) = self.img.size
        if self.column_count == 1:
            self.canv.drawInlineImage(self.img, x=-w*self.scaleFactor/2, y=0, width=w*self.scaleFactor, height=h*self.scaleFactor)
        else:
            self.canv.drawInlineImage(self.img, x=0, y=0, width=w*self.scaleFactor, height=h*self.scaleFactor)

    def drawCaption(self):
        (w,h) = self.img.size
        self.captionStyle.alignment = TA_LEFT

        if self.column_count == 1:
            self.captionPara.drawOn(self.canv, -w*self.scaleFactor/2, 0)
        else:
            self.captionPara.drawOn(self.canv, 0, 0)

    @property
    def drawWidth(self):
        return self.width

    @property
    def drawHeight(self):
        caption_height = self.captionPara.wrap(self.width, 100)[1] + self.captionGap
        return self.figureHeight + caption_height

    def _restrictSize(self,aW,aH):
        if self.drawWidth>aW+_FUZZ or self.drawHeight>aH+_FUZZ:
            self._oldDrawSize = self.drawWidth, self.drawHeight
            factor = min(float(aW)/self.drawWidth,float(aH)/self.drawHeight)
            self.drawWidth *= factor
            self.drawHeight *= factor
        return self.drawWidth, self.drawHeight

    def _unRestrictSize(self):
        dwh = getattr(self, '_oldDrawSize', None)
        if dwh:
            self.drawWidth, self.drawHeight = dwh

# Article Template Class
# This gives us a table of contents based on heading level.
class ArticleTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)

    def registerTOC(self, flowable):
        text = flowable.getPlainText()
        style = flowable.style.name
        unique_key = uuid4().hex
        self.canv.showOutline()
        self.canv.bookmarkPage(unique_key)
        if style == 'Heading1':
            self.canv.addOutlineEntry(text, unique_key, level=0, closed=None)
        elif style == 'Heading2':
            self.canv.addOutlineEntry(text, unique_key, level=1, closed=None)
        elif style == 'Heading3':
            self.canv.addOutlineEntry(text, unique_key, level=2, closed=None)

    def afterFlowable(self, flowable):
        "Registers TOC entries."
        if isinstance(flowable, Paragraph):
            self.registerTOC(flowable)
        elif isinstance(flowable, ImageAndFlowables):
            for i in flowable._content:
                if isinstance(i, Paragraph):
                    self.registerTOC(i)

# Class for automatically generating a PDF from the content of the product
class AutoPDF(object):

    # Provides the limited subset of HTML content used by the PDF generator
    space_before_punctuation_re = re.compile(u"\s+([.;:,!?])", re.I|re.M)

    # Page margin
    margin = 36

    # Standard padding for document elements
    element_padding = 6

    def __init__(self, context):
        self.context = context
        self.site = getSite()
        self.styles = self.getStyleSheet()

        # Get document attributes
        self.title = self.context.title
        self.description = self.context.description
        self.html = self.getArticleHTML()

        # Create document
        self.pdf_file = BytesIO()

        # Debug for formatting boundary
        self.showBoundary=0

        # Create document object
        self.doc = ArticleTemplate(self.pdf_file,
                              pagesize=letter,
                              title=self.title,
                              showBoundary=self.showBoundary,
                              rightMargin=self.margin,
                              leftMargin=self.margin,
                              topMargin=self.margin,
                              bottomMargin=self.margin)

    # portal_transforms will let us convert HTML into plain text
    @property
    def portal_transforms(self):
        return getToolByName(self.context, 'portal_transforms')

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')
    
    def getPloneImageObject(self, src):
        if isinstance(src, unicode):
            src = src.encode('utf-8')
        
        if src.startswith('resolveuid/'):
            uid = src[len('resolveuid/'):]
            
            results = self.portal_catalog.searchResults({'UID' : uid})
            
            if results:
                return results[0].getObject()
        
        
        else:
            try:        
                return self.site.restrictedTraverse(src)
            except:
                pass
        
        return None

    # Returns the column count value from the context
    def getColumnCount(self):

        column_count = 2

        if hasattr(self.context, 'pdf_column_count'):
            column_count = getattr(self.context, 'pdf_column_count', '2')

        try:
            column_count = int(column_count)
        except:
            column_count = 2

        return column_count

    # Returns the SKU from the context
    def getSKU(self):
        v = getattr(self.context, 'sku', '')

        if v:
            return v.strip().upper()

        return ''

    # Returns the series from the context
    def getSeries(self):
        v = getattr(self.context, 'pdf_series', '')

        if v:
            return v.strip()

        return ''

    # Returns '[SKU].pdf', or '[getId()].pdf' as the filename
    def getFilename(self):

        filename = self.getSKU()

        if not filename:
            filename = self.context.getId()

        return '%s.pdf' % filename

    @property
    def tag_to_style(self):
        # Equivalent PDF paragraph styles for HTML
        return {
            'h2' : 'Heading2',
            'h3' : 'Heading3',
            'h4' : 'Heading4',
            'h5' : 'Heading5',
            'h6' : 'Heading6',
            'p' : 'Normal'
        }

    # Returns the plain (non-HTML) text for an item.  Used at the lowest level
    # of the DOM tree because it doesn't preserve any HTML formatting
    def getItemText(self, item):
        if isinstance(item, Tag):
            return self.portal_transforms.convert('html_to_text', repr(item)).getData()
        elif isinstance(item, NavigableString):
            return str(item).strip()
        else:
            return str(item).strip()


    # Traverses the HTML structure and returns the adjusted HTML for the PDF
    def getInlineContents(self, item):

        p_contents = []

        for i in item.contents:

            if isinstance(i, Tag):

                item_type = i.name

                if item_type in ['b', 'strong', 'i', 'em', 'super', 'sub', 'a']:

                    for a in ['class', 'title', 'rel']:
                        if i.get(a):
                            del i[a]

                    if item_type == 'strong':
                        i.name = 'b'
                    elif item_type == 'em':
                        i.name = 'i'
                    elif item_type == 'a':
                        i.name = 'link'

                        if not (i['href'].startswith('http') or i['href'].startswith('mailto')):
                            i['href'] = urljoin(self.context.absolute_url(), i['href'])

                        # Wouldn't it be nice to underline the links?
                        i['color'] = 'blue'

                    if i.string:
                        p_contents.append(repr(i))
                    else:
                        p_contents.append(self.getInlineContents(i))
                else:
                    p_contents.append(self.getItemText(i))

            elif isinstance(i, NavigableString):
                p_contents.append(str(i).strip())

        contents = " ".join(p_contents)

        return self.space_before_punctuation_re.sub(r"\1", contents)

    # Returns structure containing table data when passed a BeautifulSoup
    # <table> element.
    def getTableData(self, item):

        def getCellSpan(cell):
            colspan = int(cell.get('colspan', 1))
            rowspan  = int(cell.get('rowspan', 1))
            return (colspan, rowspan)

        th_bg = HexColor('#CCCCCC')
        th_text = HexColor('#000000')
        grid = HexColor('#999999')

        table_data = []
        table_style = []

        r_index = 0

        for tr in item.findAll('tr'):
            c_index = 0

            table_row = []

            for i in tr.findAll('th'):
                table_row.append(Paragraph(self.getInlineContents(i), self.styles['TableHeading']))
                (colspan, rowspan) = getCellSpan(i)
                c_max = c_index + colspan - 1
                r_max = r_index + rowspan - 1
                table_style.extend([
                    ('FONTNAME', (c_index,r_index), (c_index,r_index), 'Times-Bold'),
                    ('FONTSIZE', (c_index,r_index), (c_index,r_index), 9),
                    ('BACKGROUND', (c_index,r_index), (c_index,r_index), th_bg),
                    ('GRID', (c_index,r_index), (c_max,r_max), 0.5, grid),
                    ('TEXTCOLOR', (c_index,r_index), (c_index,r_index), th_text),
                    ('LEFTPADDING', (c_index,r_index), (c_index,r_index), 3),
                    ('RIGHTPADDING', (c_index,r_index), (c_index,r_index), 3),
                    ('SPAN', (c_index,r_index), (c_max,r_max)),
                    ]
                )
                c_index = c_index + 1

            for i in tr.findAll('td'):

                td_align = i.get('align', 'LEFT').upper()

                if td_align == 'RIGHT':
                    p = Paragraph(self.getInlineContents(i), self.styles['TableDataRight'])
                else:
                    p = Paragraph(self.getInlineContents(i), self.styles['TableData'])

                p.hAlign = td_align

                table_row.append(p)

                (colspan, rowspan) = getCellSpan(i)
                c_max = c_index + colspan - 1
                r_max = r_index + rowspan - 1

                table_style.extend([
                    ('GRID', (c_index,r_index), (c_max,r_max), 0.5, grid),
                    ('FONTNAME', (c_index,r_index), (c_index,r_index), 'Times-Roman'),
                    ('FONTSIZE', (c_index,r_index), (c_index,r_index), 9),
                    ('LEFTPADDING', (c_index,r_index), (c_index,r_index), 3),
                    ('RIGHTPADDING', (c_index,r_index), (c_index,r_index), 3),
                    ('SPAN', (c_index,r_index), (c_max,r_max)),
                    ('ALIGN', (c_index,r_index), (c_index,r_index), td_align),
                    ]
                )

                c_index = c_index + 1

            table_data.append(table_row)
            r_index = r_index + 1

        caption = item.find('caption')

        return (table_data, TableStyle(table_style), caption)


    # Provides the PDF entities for the corresponding HTML tags.
    def getContent(self, item, bump_headings=False):
        pdf = []
        if isinstance(item, Tag):
            className=item.get('class', '').split()
            item_type = item.name
            if item_type in ['h2', 'h3', 'h4', 'h5', 'h6']:
                item_style = self.tag_to_style.get(item_type)
                h = Paragraph(self.getItemText(item), self.styles[item_style])
                h.keepWithNext = True
                pdf.append(h)
                if item_type == 'h2' and not bump_headings:
                    hr = HRFlowable(width='100%', thickness=0.25, spaceBefore=2, spaceAfter=4, color=self.styles[item_style].textColor)
                    hr.keepWithNext = True
                    pdf.append(hr)
            elif item_type in ['table']:
                (table_data, table_style, caption) = self.getTableData(item)
                table = Table(table_data)
                table.setStyle(table_style)
                table.hAlign = 'LEFT'
                table.spaceBefore = 10
                table.spaceAfter = 10

                if caption:
                    caption_el = Paragraph(self.getInlineContents(caption), self.styles['Discreet'])
                    pdf.append(KeepTogether([table, caption_el]))
                else:
                    pdf.append(table)

            elif item_type in ['ul']:
                for i in item.findAll('li'):
                    pdf.append(Paragraph('<bullet>&bull;</bullet>%s' % self.getInlineContents(i), self.styles['BulletList']))
            elif item_type in ['ol']:
                # Sequences were incrementing based on previous PDF generations.
                # Including explicit ID and reset
                li_uuid = uuid1().hex
                for i in item.findAll('li'):
                    pdf.append(Paragraph('<seq id="%s" />. %s' % (li_uuid, self.getInlineContents(i)), self.styles['BulletList']))
                pdf.append(Paragraph('<seqReset id="%s" />' % li_uuid, self.styles['Normal']))
            elif item_type in ['p'] or (item_type in ['div'] and 'captionedImage' in className or 'callout' in className or 'pullquote' in className):

                has_image = False

                # Pull images out of items and add before
                for img in item.findAll('img'):
                    img.extract()
                    src = img['src'].replace(self.site.absolute_url(), '')

                    if src.startswith('/'):
                        src = src.replace('/', '', 1)

                    img_obj = self.getPloneImageObject(src)
                    
                    if img_obj:
                        has_image = True

                        img_data = img_obj.image.data
                        pil_image = self.getImageFromData(img_data)
                        pdf_image = self.getImage(pil_image)

                        pdf.append(pdf_image)

                # If we had an image, and the next paragraph has the
                # 'discreet' class (is a caption) then keep them together
                if has_image:
                    s = item.findNextSiblings()
                    if s and 'discreet' in s[0].get('class', ''):
                        pdf[-1].keepWithNext = True

                # Get paragraph contents
                p_contents = self.getInlineContents(item)

                # Don't add anything if no contents.
                if not p_contents:
                    pass
                elif 'callout' in className or 'pullquote' in className:
                    pdf.append(Paragraph(p_contents, self.styles['Callout']))
                elif 'discreet' in className or 'captionedImage' in className:
                    if len(pdf) and isinstance(pdf[-1], Image):
                        pdf[-1].keepWithNext = True
                    pdf.append(Paragraph(p_contents, self.styles['Discreet']))
                else:
                    pdf.append(Paragraph(p_contents, self.styles["Normal"]))

            elif item_type in ['div']:
                for i in item.contents:
                    pdf.extend(self.getContent(i))

            elif item_type == 'blockquote':
                pdf.append(Paragraph(self.getItemText(item), self.styles['Blockquote']))
            else:
                pdf.append(Paragraph(self.getItemText(item), self.styles["Normal"]))
        elif isinstance(item, NavigableString):
            if item.strip():
                pdf.append(Paragraph(item, self.styles["Normal"]))
        return pdf

    def getStyleSheet(self):

        # Header Color
        header_rgb = HexColor('#4B7D45') # Green (dark enough)

        # Callout Colors
        callout_background_rgb = HexColor('#F6F6F6')

        # Styles
        styles=getSampleStyleSheet()

        # Paragraph Font
        styles['Normal'].spaceBefore = 3
        styles['Normal'].spaceAfter = 6
        styles['Normal'].fontName = 'Times-Roman'

        # Series Heading
        styles.add(ParagraphStyle('SeriesHeading'))
        styles['SeriesHeading'].spaceBefore = 0
        styles['SeriesHeading'].spaceAfter = 2
        styles['SeriesHeading'].fontSize = 10
        styles['SeriesHeading'].textColor = (0, 0, 0)
        styles['SeriesHeading'].leading = 13
        styles['SeriesHeading'].fontName = 'Helvetica-Bold'
        styles['SeriesHeading'].textTransform = 'uppercase'

        # H1
        styles['Heading1'].fontSize = 25
        styles['Heading1'].fontName = 'Helvetica-Bold'
        styles['Heading1'].leading = 29
        styles['Heading1'].spaceBefore = 2
        styles['Heading1'].spaceAfter = 12
        styles['Heading1'].textColor = header_rgb

        # H2
        styles['Heading2'].allowWidows = 0
        styles['Heading2'].fontName = 'Helvetica-Bold'
        styles['Heading2'].fontSize = 15
        styles['Heading2'].leading = 18
        styles['Heading2'].spaceAfter = 8
        styles['Heading2'].spaceAfter = 2
        styles['Heading2'].textColor = header_rgb

        # H3
        styles['Heading3'].allowWidows = 0
        styles['Heading3'].fontName = 'Helvetica-Bold'
        styles['Heading3'].fontSize = 12
        styles['Heading3'].leading = 14
        styles['Heading3'].spaceAfter = 4
        styles['Heading3'].textColor = header_rgb

        # H4
        styles['Heading4'].allowWidows = 0
        styles['Heading4'].fontName = 'Helvetica-Bold'
        styles['Heading4'].fontSize = 10
        styles['Heading4'].leading = 12
        styles['Heading4'].spaceAfter = 6
        styles['Heading4'].textColor = header_rgb

        # Article description
        styles.add(ParagraphStyle('Description'))
        styles['Description'].spaceBefore = 6
        styles['Description'].spaceAfter = 8
        styles['Description'].fontSize = 11
        styles['Description'].fontName = 'Helvetica-Bold'
        styles['Description'].leading = 13

        # TH
        styles.add(ParagraphStyle('TableHeading'))
        styles['TableHeading'].spaceBefore = 3
        styles['TableHeading'].spaceAfter = 6
        styles['TableHeading'].fontSize = 10
        styles['TableHeading'].fontName = 'Times-Bold'

        #TD
        styles.add(ParagraphStyle('TableData'))
        styles['TableData'].spaceBefore = 3
        styles['TableData'].spaceAfter = 6
        styles['TableData'].fontSize = 10
        styles['TableData'].fontName = 'Times-Roman'

        # TD align=right
        styles.add(ParagraphStyle('TableDataRight'))
        styles['TableDataRight'].spaceBefore = 3
        styles['TableDataRight'].spaceAfter = 6
        styles['TableDataRight'].fontSize = 10
        styles['TableDataRight'].fontName = 'Times-Roman'
        styles['TableDataRight'].alignment = TA_RIGHT

        # UL
        styles.add(ParagraphStyle('BulletList'))
        styles['BulletList'].spaceBefore = 4
        styles['BulletList'].spaceAfter = 4
        styles['BulletList'].fontName = 'Times-Roman'
        styles['BulletList'].bulletIndent = 5
        styles['BulletList'].leftIndent = 17
        styles['BulletList'].bulletFontSize = 12

        # BLOCKQUOTE
        styles.add(ParagraphStyle('Blockquote'))
        styles['Blockquote'].leftIndent = 12
        styles['Blockquote'].rightIndent = 8
        styles['Blockquote'].spaceAfter = 6
        styles['Blockquote'].fontName = 'Times-Roman'

        # .discreet
        styles.add(ParagraphStyle('Discreet'))
        styles['Discreet'].fontSize = 9
        styles['Discreet'].textColor = HexColor('#717171')
        styles['Discreet'].spaceAfter = 12
        styles['Discreet'].spaceBefore = 1

        # .callout
        styles.add(ParagraphStyle('Callout'))
        styles['Callout'].fontSize = 10
        styles['Callout'].textColor = header_rgb
        styles['Callout'].spaceAfter = 20
        styles['Callout'].spaceBefore = 22
        styles['Callout'].backColor = callout_background_rgb
        styles['Callout'].borderColor = header_rgb
        styles['Callout'].borderWidth = 1
        styles['Callout'].borderPadding = (8, 12, 10, 12)
        styles['Callout'].rightIndent = 15
        styles['Callout'].leftIndent = 15

        # Statement
        styles.add(ParagraphStyle('Statement'))
        styles['Statement'].fontSize = 8
        styles['Statement'].fontName = 'Times-Roman'
        styles['Statement'].spaceAfter = 5
        styles['Statement'].leading = 10

        # Padded Image
        styles.add(ParagraphStyle('PaddedImage'))
        styles['PaddedImage'].spaceBefore = 12
        styles['PaddedImage'].spaceAfter = 12

        return styles


    # Returns a reportlab image object based on a PIL image object
    def getImage(self, img_obj, scale=True, width=None, style=None,
                 caption="", hAlign=None, body_image=True):

        if not width:
            width = self.getMaxImageWidth()

        column_count = self.getColumnCount()

        if body_image and column_count == 1:
            # Special case to make one column body images 66% of the page
            width = 1.33*width

        img_width = img_obj.width
        img_height = img_obj.height

        if scale and (img_width > width):
            img_height = (width/img_width)*img_height
            img_width = width

        if hasattr(img_obj, 'tobytes'):
            img_buffer = StringIO()
            img_obj.save(img_buffer, img_obj.format, quality=90)
            img_data = BytesIO(img_buffer.getvalue())

        elif hasattr(img_obj, 'data'):
            if hasattr(img_obj.data, 'data'):
                img_data = BytesIO(img_obj.data.data)
            else:
                img_data = BytesIO(img_obj.data)

        elif hasattr(img_obj, '_data'):
            img_data = BytesIO(img_obj._data)

        else:
            img_data = BytesIO('')

        if caption:
            img = ImageFigure(img_data, caption=caption, width=img_width, height=img_height, align="right", max_image_width=width, column_count=column_count)
        else:
            img = Image(img_data, width=img_width, height=img_height)

        if style:
            img.style = style

        if hAlign:
            img.hAlign = hAlign
        elif column_count == 1:
            img.hAlign = TA_LEFT
        else:
            img.hAlign = TA_CENTER

        return img

    def getMaxImageWidth(self):

        # Number of columns
        column_count = self.getColumnCount()

        # Document image setttings
        max_image_width = self.doc.width/column_count-(3*self.element_padding)

        if column_count <= 1:
            max_image_width = self.doc.width/2-(3*self.element_padding)

        return max_image_width

    def getArticleHTML(self):

        if self.context.Type() not in ['Article',]:
            return "<h2>Error</h2><p>%s is not a valid type.</p>" % self.context.Type()

        html = []

        pages = IArticleMarker(self.context).getPages()
        
        multi_page = len(pages) > 1

        for p in pages:

            page_type = p.Type()

            if multi_page:
                html.append('<h2>%s</h2>' % p.title)

                if p.description:
                    html.append('<p><strong>%s</strong></p>' % p.description)
                
            if page_type == 'Article Page':
                if multi_page:
                    html.append(increaseHeadingLevel(p.text.raw))
                else:
                    html.append(p.text.raw)

        return " ".join(html)

    def getResourceImage(self, path):
        img_resource = self.site.restrictedTraverse(path)

        img_data = img_resource.GET()

        return self.getImageFromData(img_data)
        
    def getImageFromData(self, data):
        return PILImage.open(StringIO(data))

    def createPDF(self):

        # Number of columns
        column_count = self.getColumnCount()

        # Grab the publication code
        publication_code = self.getSKU()

        # Grab the publication series
        publication_series = self.getSeries()

        # Get the PDF document object
        doc = self.doc

        #-------------- calculated coordinates/w/h
        extension_url_image = self.getResourceImage('++resource++agsci.atlas/images/extension-url.png')
        extension_url_image_width = 0.5*self.getMaxImageWidth()

        # Factsheet title
        title_lines = 3
        publication_series_height = 0

        if publication_series:
            # If series heading, only 2 title lines
            title_lines = 2

            # One line for the series heading
            publication_series_height = self.styles['SeriesHeading'].spaceBefore + \
                                        self.styles['SeriesHeading'].spaceAfter + \
                                        self.styles['SeriesHeading'].leading

        title_height = self.styles['Heading1'].spaceBefore + \
                       self.styles['Heading1'].spaceAfter + \
                       (title_lines * self.styles['Heading1'].leading) + \
                       publication_series_height + self.element_padding


        # Penn State/Extension Footer Image
        footer_image_width = 222.0 # 72 points/inch * 3.125"
        footer_image = self.getResourceImage('++resource++agsci.atlas/images/extension-factsheet-footer.png')
        footer_image_height = footer_image_width*(1.0*footer_image.height/footer_image.width)

        # Header and footer on first page
        def header_footer(canvas,doc):

            canvas.saveState()

            # Line under Title
            canvas.setStrokeColorRGB(0, 0, 0)

            line_y=doc.bottomMargin+doc.height-title_height

            canvas.line(doc.leftMargin+self.element_padding,
                        line_y,
                        doc.width+doc.leftMargin-self.element_padding,
                        line_y)

            # Footer
            canvas.drawImage(ImageReader(footer_image),
                             doc.leftMargin+self.element_padding,
                             72.0/2,
                             width=footer_image_width,
                             height=footer_image_height,
                             preserveAspectRatio=True,
                             mask='auto')

            canvas.restoreState()

        # Footer for pages 2 and after
        def footer(canvas,doc):
            canvas.saveState()

            canvas.setFont('Times-Roman', 9)
            canvas.drawString(self.margin, 24, "Page %d" % doc.page)

            canvas.setFont('Times-Roman', 9)
            canvas.drawRightString(doc.width+self.margin+self.element_padding,
                                   24,
                                   self.title)

            canvas.restoreState()

        # First (title) page

        title_y = doc.bottomMargin + doc.height - title_height

        title_column_y = doc.bottomMargin+footer_image_height+self.element_padding

        title_column_height = title_y - title_column_y

        title_frame_title = Frame(doc.leftMargin, title_y, doc.width, title_height, id='title_title', showBoundary=self.showBoundary)

        title_frames = [title_frame_title]

        for i in range(0,column_count):
            lm = doc.leftMargin + i * (doc.width/column_count+self.element_padding)
            w = doc.width/column_count-self.element_padding
            title_frame = Frame(lm, title_column_y, w, title_column_height, id='title_col%d' % i, showBoundary=self.showBoundary)
            title_frames.append(title_frame)

        # Remaining pages
        other_frames = []

        for i in range(0,column_count):
            lm = doc.leftMargin + i * (doc.width/column_count+self.element_padding)
            w = doc.width/column_count-self.element_padding
            other_frame = Frame(lm, doc.bottomMargin, w, doc.height, id='other_col%d' % i, showBoundary=self.showBoundary)
            other_frames.append(other_frame)

        title_template = PageTemplate(id="title_template", frames=title_frames,onPage=header_footer)
        other_template = PageTemplate(id="other_template", frames=other_frames,onPage=footer)

        doc.addPageTemplates([title_template,other_template])
        doc.handle_nextPageTemplate("other_template")

        # ---------------------------------------------------------------------
        # Convert HTML to PDF (Magic goes here)
        # ---------------------------------------------------------------------

        # Soupify
        soup = BeautifulSoup(self.html)

        # This list holds the PDF elements
        pdf = []

        # Series, page heading and description in top frame, then framebreak
        # into two columns.  Optionally add the description to the body if the
        # flag is set.

        if publication_series:
            pdf.append(Paragraph(publication_series, self.styles['SeriesHeading']))

        pdf.append(Paragraph(self.title, self.styles["Heading1"]))

        # Move to next frame
        pdf.append(FrameBreak())

        if self.description:
            pdf.append(Paragraph(self.description, self.styles['Description']))

        # Push headings to the smallest level

        # If we have an h2, but not an h3 or h4, bump the heading styles down.
        attrs = ['allowWidows', 'fontName', 'fontSize', 'leading', 'spaceAfter', 'textColor', ]

        bump_headings = False

        if '<h2' in self.html and not '<h3' in self.html and not '<h4' in self.html:

            bump_headings = True

            heading_tags = sorted([x for x in self.tag_to_style.keys() if x.startswith('h')])

            for i in range(0, len(heading_tags) - 1):
                from_style = self.tag_to_style[heading_tags[i]]
                to_style = self.tag_to_style[heading_tags[i+1]]
                for a in attrs:
                    self.styles[from_style].__dict__[a] = self.styles[to_style].__dict__[a]



        # Loop through Soup contents
        for item in soup.contents:
            pdf.extend(self.getContent(item, bump_headings=bump_headings))

        # Embed lead images in paragraphs if we're a single column
        if column_count == 1:
            for i in range(1,len(pdf)-1):
                if isinstance(pdf[i], ImageFigureBase):

                    paragraphs = []

                    for j in range(i+1, len(pdf)-1):
                        if isinstance(pdf[j], Paragraph) or isinstance(pdf[j], HRFlowable):
                            paragraphs.append(pdf[j])
                            pdf[j] = None
                        else:
                            break

                    if paragraphs:

                        pdf[i].hAlign="RIGHT"

                        img_paragraph = ImageAndFlowables(pdf[i], paragraphs,imageLeftPadding=self.element_padding)

                        pdf[i] = img_paragraph

            while None in pdf:
                pdf.remove(None)

        # Authors
        # TODO

        # All done with contents, appending line and statement
        pdf.append(HRFlowable(width='100%', spaceBefore=4, spaceAfter=4))

        # Extension logo
        pdf.append(self.getImage(extension_url_image, 
                                 scale=True, width=extension_url_image_width,
                                 style=self.styles['PaddedImage'], 
                                 hAlign='LEFT', body_image=False))

        # Choose which statement
        aa_statement = """Penn State is an equal opportunity, affirmative action employer, and is committed to providing employment opportunities to all qualified applicants without regard to race, color, religion, age, sex, sexual orientation, gender identity, national origin, disability or protected veteran status."""

        statement_text = ("""Penn State College of Agricultural Sciences research and extension programs are funded in part by Pennsylvania counties, the Commonwealth of Pennsylvania, and the U.S. Department of Agriculture.

        Where trade names appear, no discrimination is intended, and no endorsement by Penn State Extension is implied.

        <b>This publication is available in alternative media on request.</b>

        %s

        &copy The Pennsylvania State University %d

        """ % (aa_statement, DateTime().year())).split("\n")

        # Append the publication code, if it exists
        if publication_code:
            statement_text.append("Code: %s" % publication_code)

        # Create paragraphs from the statement text
        for s in statement_text:
            if s.strip():
                pdf.append(Paragraph(s, self.styles['Statement']))

        # Create PDF - multibuild instead of build for table of contents
        # functionality
        doc.multiBuild(pdf)

        # Pull PDF binary bits into variable, close file handle and return
        pdf_value = self.pdf_file.getvalue()

        # Close the PDF file
        self.pdf_file.close()

        return pdf_value
