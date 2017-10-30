from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.content import ContentHistoryView
from time import time

from agsci.atlas.utilities import getBodyHTML
from agsci.atlas.content.adapters import ArticleDataAdapter
from .scheduled import ScheduledNotificationConfiguration

from Products.CMFPlone.utils import safe_unicode
import textwrap

class ProductTextDump(ScheduledNotificationConfiguration):

    wrap_characters = 72

    # Returns the portal_transforms tool
    @property
    def portal_transforms(self):
        return getToolByName(self.context, 'portal_transforms')

    # Converts raw HTML to text
    def html_to_text(self, html=None):
        if html:
            return self.portal_transforms.convert('html_to_text', html).getData()
        return ''

    # Get the product title/description
    @property
    def title_description(self):

        # Initialize rv
        rv = []

        # Add the title to rv
        title = self.context.title

        rv.extend(textwrap.wrap(title, self.wrap_characters))
        rv.append('')

        # Add description, if it exists
        description = self.context.description

        if description:
            rv.extend(textwrap.wrap(description, self.wrap_characters))
            rv.append('')

        # Return list of lines
        return rv

    # Empty by default
    @property
    def full_text(self):
        return []

    def __call__(self):

        # Initialize rv
        rv = []

        # Get title/description
        rv.extend(self.title_description)

        # Get full text
        rv.extend(self.full_text)

        # All lines to unicode
        rv = [safe_unicode(x) for x in rv]

        # Remove leading/trailing whitespace
        rv = [" ".join(x.strip().split()) for x in rv]

        # Return one unicode field
        return u"\n".join(rv)

class ArticleTextDump(ProductTextDump):

    # Compile the full text of the article
    @property
    def full_text(self):

        # Initialize rv
        rv = []

        # Add page HTML
        for page in ArticleDataAdapter(self.context).getPages():
            html = getBodyHTML(page)

            if html:
                text = self.html_to_text(html)

                for _ in text.split("\n"):
                    if _.strip():
                        rv.extend(textwrap.wrap(_, self.wrap_characters))
                        rv.append('')

        # Return list of lines
        return rv