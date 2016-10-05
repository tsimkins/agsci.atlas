from Acquisition import aq_base
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from functools import wraps
from urlparse import urlparse
from zope.annotation.interfaces import IAnnotations
from zope.component import subscribers
from zope.globalrequest import getRequest
from zope.interface import Interface

from agsci.atlas.constants import ACTIVE_REVIEW_STATES
from agsci.atlas.utilities import truncate_text
from agsci.leadimage.interfaces import ILeadImageMarker as ILeadImage

from .error import HighError, MediumError, LowError
from ..vocabulary.calculator import AtlasMetadataCalculator

import re

alphanumeric_re = re.compile("[^A-Za-z0-9]+", re.I|re.M)

# Cache errors on HTTP Request, since we may be calling this multiple times.
# Ref: http://docs.plone.org/manage/deploying/performance/decorators.html#id7
def getValidationErrors(context):

    request = getRequest()

    key = "product-validation-errors-%s" % context.UID()

    cache = IAnnotations(request)

    data = cache.get(key, None)

    if not isinstance(data, list):
        data = _getValidationErrors(context)
        cache[key] = data

    return data

def _getValidationErrors(context):

    errors = []
    levels = ['High', 'Medium', 'Low']

    for i in subscribers((context,), IContentCheck):
        try:
            for j in i:
                errors.append(j)
        except Exception as e:
            errors.append(
                LowError(i, u"Internal error running check: '%s: %s'" % (e.__class__.__name__, e.message))
            )

    # Sort first on the hardcoded order
    errors.sort(key=lambda x: x.sort_order)

    # Then sort on the severity
    errors.sort(key=lambda x: levels.index(x.level))

    return errors

# This is a decorator (@context_memoize) that memoizes no-parameter methods based
# on the method name and UID for the context. The purpose is to not have to call
# ".html", ".text", ".soup", etc. many times for many different checks.
#
# Rudimentary tracking shows a 30% increase in performance, which will be more
# apparent as we're running more checks.
def context_memoize(func):

    @wraps(func)
    def func_wrapper(name):
        key = getKey(func, name)
        return getCachedValue(func, key, name)

    def getKey(func, name):
        uid = name.context.UID()
        method = func.__name__
        return '-'.join([method, uid])

    def getCachedValue(func, key, name):
        request = getRequest()

        cache = IAnnotations(request)

        if cache.has_key(key):
            return cache.get(key)

        cache[key] = func(name)

        return cache[key]

    return func_wrapper


# Interface for warning subscribers
class IContentCheck(Interface):
    pass


# Base class for content check
class ContentCheck(object):

    # Title for the check
    title = "Default Check"

    # Description for the check
    description = ""

    # Action to remediate the issue
    action =""

    # Render the output as HTML.
    render = False

    # Sort order (lower is higher)
    sort_order = 0

    def __init__(self, context):
        self.context = context

    @property
    def error_code(self):
        return self.__class__.__name__

    @property
    def request(self):
        return getRequest()

    def value(self):
        """ Returns the value of the attribute being checked """

    def check(self):
        """ Performs the check and returns HighError/MediumError/LowError/None """

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal_transforms(self):
        return getToolByName(self.context, 'portal_transforms')

    def __iter__(self):
        return self.check()

# Validates the product title length
class TitleLength(ContentCheck):

    title = "Product Title Length"
    description = "Titles should be no more than 60 characters."
    action = "Edit the title to be no more than 60 characters.  For short titles, add more detail."

    # Sort order (lower is higher)
    sort_order = 1

    def value(self):
        return len(self.context.title)

    def check(self):
        v = self.value()

        if v > 128:
            yield HighError(self, u"%d characters is too long." % v)
        elif v > 80:
            yield MediumError(self, u"%d characters is too long." % v)
        elif v > 60:
            yield LowError(self, u"%d characters is too long." % v)
        elif v < 16:
            yield LowError(self, u"%d characters may be too short." % v)


# Validates the product description length
class DescriptionLength(ContentCheck):

    title = "Product Description Length"
    description = "Product must have a description, which should be a maximum of 160 characters."
    action = "Edit the description to be no more than 160 characters.  For short or missing descriptions, add more detail."

    # Sort order (lower is higher)
    sort_order = 1

    def value(self):
        return len(self.context.description)

    def check(self):

        v = self.value()

        if v > 255:
            yield HighError(self, u"%d characters is too long." % v)
        elif v > 200:
            yield MediumError(self, u"%d characters is too long." % v)
        elif v > 160:
            yield LowError(self, u"%d characters is too long." % v)
        elif v == 0:
            yield HighError(self, u"A description is required for this product.")
        elif v < 32:
            yield LowError(self, u"%d characters may be too short." % v)


# Validates that the right number of EPAS categories are selected
# Parent class with basic logic
class ProductEPAS(ContentCheck):

    title = "EPAS Selections"
    fields = ('atlas_state_extension_team', 'atlas_program_team', 'atlas_curriculum')
    action = "Under the 'Categorization' tab, select the appropriate EPAS information"

    # Sort order (lower is higher)
    sort_order = 3

    required_values = [
        (1,1,1),
    ]

    # Number of selections for each field.
    def value(self):
        try:
            return tuple([len(getattr(self.context, x, [])) for x in self.fields])
        except TypeError:
            return (0,0,0)

    def check(self):
        v = self.value()

        if v not in self.required_values:
            yield HighError(self, u"Selections incorrect.")


# Validates that the right number of EPAS categories are selected
class ArticleEPAS(ProductEPAS):

    description = "Articles should have one each of State Extension Team, Program Team, and Curriculum selected."


class VideoEPAS(ProductEPAS):

    description = "Videos should have one each of State Extension Team, Program Team, and Curriculum selected."


class ProductCategoryValidation(ContentCheck):

    # Sort order (lower is higher)
    sort_order = 2

    category_fields = [1, 2]

    @property
    def title(self):
        return "Category Level %d" % self.category_fields[-1]

    @property
    def description(self):
        return "%s should be assigned when available." % self.title

    action = "Under the 'Categorization' tab, select the appropriate Categories."

    def value(self):
        # Get the category level values
        v1 = getattr(self.context, 'atlas_category_level_%d' % self.category_fields[0] , [])
        v2 = getattr(self.context, 'atlas_category_level_%d' % self.category_fields[1], [])

        return (v1, v2)

    def check(self):
        # Get the level 1 and level 2 values
        (v1, v2) = self.value()

        # Iterate through the level 1 values.  If a level 2 value is available
        # for that level 1, but no level 1s are selected, throw an error
        mc = AtlasMetadataCalculator('CategoryLevel%d' % self.category_fields[1])
        vocabulary = mc.getTermsForType()

        for i in v1:
            available_v2 = [x.value for x in vocabulary._terms if x.value.startswith('%s:' % i)]

            if available_v2:
                if not (set(v2) & set(available_v2)):

                    yield HighError(self, (u"Values for Category Level %d '%s' " +
                                     u"are available, but not selected. Best practice " +
                                     u"is to select all levels of categories where " +
                                     u"options are available.") % (self.category_fields[1], i))


# Validates that a Category Level 1 is selected for all.
class ProductCategory1(ProductCategoryValidation):

    category_fields = [1,]

    title = "Category Level %d" % category_fields[-1]
    description = "%s should be assigned." % title

    def value(self):
        return getattr(self.context, 'atlas_category_level_%d' % self.category_fields[0] , [])

    def check(self):
        # Get the level 1 and level 1 values
        v1 = self.value()

        if not v1:
            yield HighError(self, u"Category Level 1 must be assigned.")


# Validates that a Category Level 2 is selected for all Category Level 1's
# that are available.
class ProductCategory2(ProductCategoryValidation):

    pass


# Validates that a Category Level 3 is selected for all Category Level 2's
# that are available.
class ProductCategory3(ProductCategoryValidation):

    category_fields = [2, 3]


# Checks for issues in the text.  This doesn't actually check, but is a parent
# class for other checks.
class BodyTextCheck(ContentCheck):

    # Title for the check
    title = "HTML: Body Text Check"

    # Description for the check
    description = ""

    # Sort order (lower is higher)
    sort_order = 10

    # h1 - h6
    all_heading_tags = ['h%d' % x for x in range(1,7)]

    @property
    def contents(self):
        # Strip out Acquisition layer
        if hasattr(aq_base(self.context), 'getPages'):
            return self.context.getPages()

        return []

    def getHTML(self, o):
        if hasattr(o, 'text') and hasattr(o.text, 'raw'):
            return safe_unicode(o.text.raw)

        return ''

    def html_to_text(self, html):
        text = self.portal_transforms.convert('html_to_text', html).getData()
        text = " ".join(text.strip().split())
        return safe_unicode(text)

    def soup_to_text(self, soup):
        html = safe_unicode(repr(soup))
        text = self.portal_transforms.convert('html_to_text', html).getData()
        text = " ".join(text.strip().split())
        return safe_unicode(text)

    def value(self):
        return self.html

    @property
    @context_memoize
    def soup(self):
        return BeautifulSoup(self.html)

    @property
    @context_memoize
    def html(self):
        v = [
            self.getHTML(self.context)
        ]

        for o in self.contents:
            v.append(self.getHTML(o))

        v = ' '.join(v)

        return safe_unicode(v)

    @property
    @context_memoize
    def text(self):
        return self.html_to_text(self.html)

    def toWords(self, text):
        text = alphanumeric_re.sub(' ', text.lower()).split()
        return list(set(text))

    @property
    def words(self):
        return self.toWords(self.text)

    def check(self):
        pass

    def getLinks(self):
        return self.soup.findAll('a')

    def getImages(self):
        return self.soup.findAll('img')

    def getHeadings(self):
        return self.soup.findAll(self.all_heading_tags)

# Checks for appropriate heading level hierarchy, e.g. h2 -> h3 -> h4
class BodyHeadingCheck(BodyTextCheck):

    def value(self):
        return self.getHeadings()

# Generic Image check that returns all <img> tags as the value()
class BodyImageCheck(BodyTextCheck):

    def value(self):
        return self.soup.findAll('img')


# Generic Image check that returns all <img> tags as the value()
class BodyLinkCheck(BodyTextCheck):

    def value(self):
        return self.soup.findAll('a')


# Checks for appropriate heading level hierarchy, e.g. h2 -> h3 -> h4
class HeadingLevels(BodyHeadingCheck):

    # Title for the check
    title = "HTML: Heading Levels"

    # Description for the check
    description = "Validates that the heading level hierarchy is correct."

    # Remedial Action
    action = "In the product text (including any pages for Articles), validate that the heading levels are in the correct order, and none are skipped."

    def check(self):

        headings = self.value()

        # Get heading tag object names (e.g. 'h2')
        heading_tags = [x.name for x in headings]

        # If no heading tags to check, return
        if not heading_tags:
            return

        # Check if we have an h1 (not permitted)
        if 'h1' in heading_tags:
            yield MediumError(self, "An <h1> heading is not permitted in the body text.")

        # Validate that the first tag in the listing is an h2
        if heading_tags[0] != 'h2':
            yield MediumError(self, "The first heading in the body text must be an <h2>.")

        # Check for heading tag order, and ensure we don't skip any
        for i in range(0, len(heading_tags)-1):
            this_heading = heading_tags[i]
            next_heading = heading_tags[i+1]

            this_heading_idx = self.all_heading_tags.index(this_heading)
            next_heading_idx = self.all_heading_tags.index(next_heading)

            if next_heading_idx > this_heading_idx and next_heading_idx != this_heading_idx + 1:
                heading_tag_string = "<%s> to <%s>" % (this_heading, next_heading) # For error message
                yield MediumError(self, "Heading levels in the body text are skipped or out of order: %s" % heading_tag_string)


# Check for heading length
class HeadingLength(BodyHeadingCheck):

    # Title for the check
    title = "HTML: Heading Text Length"

    # Description for the check
    description = "Validates that the heading text is not too long. "

    # Remedial Action
    action = "Ensure that headings are a maximum of 120 characters, and ideally 60 characters or less."

    # Warning levels for h2 and h3.  Allow h3's to be slightly longer before a warning is triggered.
    warning_levels = {
                        'h2' : 60,
                        'h3' : 100,
    }

    def check(self):
        headings = self.getHeadings()

        for i in headings:
            text = self.soup_to_text(i)
            warning_length = self.warning_levels.get(i.name, 99999)

            v = len(text)

            if v > 200:
                yield HighError(self, u"Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > 120:
                yield MediumError(self, u"Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > warning_length:
                yield LowError(self, u"Length of %d characters for <%s> heading '%s' may be too long." % (v, i.name, text))


# Verifies that the product title is unique for that type of product
class ProductUniqueTitle(ContentCheck):

    # Title for the check
    title = "Unique Product Title"

    # Description for the check
    description = "Validates that the product title is unique within a product type."

    action = "Add additional context to the title, or combine multiple related articles."

    # Sort order (lower is higher)
    sort_order = 4

    # Render the output as HTML.
    render = True

    def value(self):

        # Remove parenthesis from actual title to avoid catalog errors.
        _title = self.context.title.replace('(', '').replace(')', '')

        # Query catalog for all objects of the same type with the same title
        results = self.portal_catalog.searchResults({'Type' : self.context.Type(),
                                                     'Title' : _title,
                                                     'review_state' :  ACTIVE_REVIEW_STATES})

        # Removes the entry for this product
        results = filter(lambda x: x.UID != self.context.UID(), results)

        # Find titles that exactly match.
        results = filter(lambda x: safe_unicode(x.Title.strip().lower()) == safe_unicode(self.context.title.strip().lower()), results)

        # Returns the rest of the matching brains
        return results

    def check(self):
        value = self.value()
        if value:
            urls = "<ul>%s</ul>" % " ".join(["<li><a href='%s'>%s</a></li>" % (x.getURL(), x.Title) for x in value])
            yield MediumError(self, u"%s(s) with a duplicate title found at: %s" % (self.context.Type(), urls))


# Verifies that the product owner is a valid person in the directory.
class ProductValidOwners(ContentCheck):

    # Title for the check
    title = "Valid Owner(s)"

    # Description for the check
    description = "Validates that the owner id(s) are active individuals in the directory"

    action = "Under the 'Ownership' tab, ensure that all of the ids listed in the 'Owners' field are active in the directory"

    # Sort order (lower is higher)
    sort_order = 5

    def value(self):
        # Get the owners
        owners = getattr(self.context, 'owners', [])

        # Filter out blank owners
        return [x for x in owners if x]

    def validPeopleIds(self):
        # Get the current date/time
        now = DateTime()

        # Search for non-expired people
        results = self.portal_catalog.searchResults({'Type' : 'Person',
                                                     'expires' : {'range' : 'min',
                                                                  'query' : now
                                                                 }
                                                     })

        # Get the usernames
        user_ids = map(lambda x: getattr(x.getObject(), 'username', None), results)

        # Filter out empty usernames
        user_ids = [x for x in user_ids if x]

        return user_ids

    def check(self):
        # Get the owners, and the valid users
        value = set(self.value())
        user_ids = set(self.validPeopleIds())

        # Find any invalid users
        invalid_user_ids = list(value - user_ids)

        # Raise a warning if invalid users are found.
        if invalid_user_ids:
            invalid_user_ids = ", ".join(invalid_user_ids)
            yield MediumError(self, u"Product owner id(s) '%s' are invalid." % invalid_user_ids)


# Checks for embedded videos (iframe, embed, object, etc.) in the text.
# Raises a High if there's a YouTube or Vimeo video (specifically) or a
# Low otherwise
class EmbeddedVideo(BodyTextCheck):

    # Title for the check
    title = "HTML: Embedded Video"

    # Description for the check
    description = "Videos (e.g. YouTube videos) should be created as 'Videos' in an article, rather than embedded in the HTML of Article Pages."

    # Action
    action = "Remove video embed code (iframe) from page, and create a 'Video' inside the article."

    # Video URLs
    video_urls = ['youtube.com', 'vimeo.com']

    def check(self):

        embeds = self.soup.findAll(['object', 'iframe', 'embed',])

        for i in embeds:
            if i.name == 'iframe':
                src = i.get('src', '')
                if any([x in src for x in self.video_urls]):
                    yield HighError(self, 'Found embedded video in body text.')

        if embeds:
            yield LowError(self, 'Found embedded content (iframe, embed, or object) in body text.')


# Prohibited words and phrases. Checks for individual words, phrases, and regex patterns in body text.
class ProhibitedWords(BodyTextCheck):

    title = "HTML: Words/phrases to avoid."

    description = "In order to follow style or editoral standards, some words (e.g. 'PSU') should not be used."

    action = "Replace the words/phrases identified with appropriate alternatives."

    # List of individual words (alphanumeric only, will be compared case-insenstive.)
    find_words = ['PSU',]

    # List of phrases, will be checked for 'in' body text.
    find_phrases = ['Cooperative Extension',]

    # Regex patterns.  These are probably 'spensive.
    find_patterns = ['https*://',]

    def check(self):
        # Get a list of individual
        words = self.words
        text = self.text.lower()

        for i in self.find_words:
            if i.lower() in words:
                yield LowError(self, 'Found word "%s" in body text.' % i)

        for i in self.find_phrases:
            if i.lower() in text:
                yield LowError(self, 'Found phrase "%s" in body text.' % i)

        for i in self.find_patterns:
            i_re = re.compile('(%s)' %i, re.I|re.M)
            _m = i_re.search(text)

            if _m:
                yield LowError(self, 'Found "%s" in body text.' % _m.group(0))


# Verifies that a lead image is assigned to the product
class HasLeadImage(ContentCheck):

    title = "Lead Image"

    description = "A quality lead image is suggested to provide a visual connection for the user, and to display in search results."

    action = "Please add a quality lead image to this product."

    # Sort order (lower is higher)
    sort_order = 5

    def value(self):
        return ILeadImage(self.context).has_leadimage

    def check(self):
        if not self.value():
            yield LowError(self, 'No lead image found')


# Checks for instances of inappropriate link text in body
class AppropriateLinkText(BodyLinkCheck):

    title = 'HTML: Appropriate Link Text'

    description = "Checks for common issues with link text (e.g. using the URL as link text, 'click here', 'here', etc.)"

    action = "Linked text should be a few words that describe the content that exists at the link."

    find_words = ['click', 'http://', 'https://', 'here',]

    find_words = [x.lower() for x in find_words]

    def value(self):
        data = []

        for a in super(AppropriateLinkText, self).value():
            data.append(self.soup_to_text(a))

        return data

    def check(self):
        for i in self.value():
            link_words = self.toWords(i)
            data = []
            for j in link_words:
                if j in self.find_words:
                    yield LowError(self, 'Inappropriate Link Text "%s" (found "%s")' % (i, j))

# Checks for cases where an image is linked to something
class ImageInsideLink(BodyLinkCheck):

    title = 'HTML: Image Inside Link'

    description = "Checks for <img> tags inside a link (<a> tag).  Images should not be used inside of links."

    action = "Remove link tag from around image."

    def value(self):
        images = []

        for a in super(ImageInsideLink, self).value():
            images.extend(a.findAll('img'))

        return len(images)

    def check(self):
        found_images = self.value()

        if found_images:
            yield LowError(self, 'Found %d images inside of links.' % found_images)


# Checks for cases where an image is linked to something
class ExternalAbsoluteImage(BodyImageCheck):

    title = 'HTML: Image with an external or absolute URL'

    description = "Checks for <img> tags that reference images outside the site, or use a URL path rather than Plone's internal method."

    action = "Use the rich text editor to select an image rather than the HTML source code."

    def check(self):
        for img in self.value():
            src = img.get('src', '')
            if not src.startswith('resolveuid'):
                yield LowError(self, 'Image source of "%s" references an external/absolute image.' % src)


# Checks for cases where an image is linked to something
class ResizedImage(BodyImageCheck):

    title = 'HTML: Image is resized using the rich text editor.'

    description = "Checks for <img> tags that use Plone's resizing.  All images should be full size."

    action = "Select the 'Original' size for this image in the rich text editor."

    def check(self):
        for img in self.value():
            src = img.get('src', '')
            if src.startswith('resolveuid') and '/@@images/' in src:
                yield LowError(self, 'Image "%s" uses Plone\'s resizing' % src)


# Checks for cases where an image is inside a paragraph that has text, but does not have a discreet tag.
class ImageInsideTextParagraph(BodyImageCheck):

    title = "HTML: Image inside a paragraph"

    description = "Checks for <img> tags mixed in with paragraphs of text."

    action = "Use the rich text editor to separate the image into a standalone paragraph of class 'discreet' containing only the image caption."

    def check(self):
        # Iterate through all images in HTML
        for img in self.value():

            # Find the image's parent paragraph
            p = img.findParent('p')

            if p:
                p_class = p.get('class', '').strip()
                p_text = self.soup_to_text(p)

                if p_text:

                    p_text = truncate_text(p_text, 32)

                    if p_class and p_class == 'discreet':

                        if not p.find('br'):
                            yield LowError(self, 'Image and caption "%s" needs a <br /> between image and text.' % p_text)
                    else:
                        yield LowError(self, 'Paragraph with image and text "%s" should be of class "discreet" and contain only the caption.' % p_text)

            else:
                yield LowError(self, 'Image is not inside a <p> tag.')


# Checks for cases where a heading has a 'strong' or 'b' tag inside
class BoldHeadings(BodyHeadingCheck):

    title = 'HTML: Bold text inside headings.'

    description = "Headings should not contain bold text."

    action = "Remove bold text from headings"

    def check(self):
        for h in self.value():
            if h.findAll(['strong', 'b']):
                yield LowError(self, 'Heading %s "%s" contains bold text' % (h.name, self.soup_to_text(h)))


# Checks for cases where a heading has a 'strong' or 'b' tag inside
class HeadingsInBold(BoldHeadings):

    title = 'HTML: Headings inside bold text.'

    description = "Headings should not be inside bold text."

    action = "Remove bold text from around headings"

    def value(self):
        return self.soup.findAll(['strong', 'b'])

    def check(self):
        for b in self.value():
            for h in b.findAll(self.all_heading_tags):
                yield LowError(self, 'Heading %s "%s" inside bold text' % (h.name, self.soup_to_text(h)))

# Generic Image check that returns all <img> tags as the value()
class InternalLinkCheck(BodyLinkCheck):

    title = 'Internal Links'

    description = "Checks for links with no domain, or links to an extension.psu.edu URL"

    action = "Link internally using the text editor functionality.  Do not link to internal content by URL."

    domains = ['extension.psu.edu', 'cms.extension.psu.edu',
               'www.extension.psu.edu', 'pubs.cas.psu.edu', ]

    def check(self):
        for a in self.value():
            href = a.get('href', '')
            if href:

                if href.startswith('resolveuid'):
                    continue

                if href.startswith('mailto:'):
                    continue

                parsed_url = urlparse(href)
                domain = parsed_url.netloc
                url_text = self.soup_to_text(a)

                if domain in self.domains:
                    yield LowError(self, 'Link URL "%s" (%s) links to Extension site domain.' % (url_text, href))
                elif not domain:
                    yield LowError(self, 'Link URL "%s (%s)" is internal.' % (url_text, href))

# Checks for multiple sequential breaks inside a paragraph
class ParagraphMultipleBreakSequenceCheck(BodyTextCheck):

    title = 'HTML: Multiple sequential breaks inside a paragraph.'

    description = "Paragraphs should be contained in individual <p> tags, not separated by 'double breaks.'"

    action = "Replace '<br /><br />' with '</p><p>' in rich text editor."

    def check(self):

        # Iterate through all paragraphs in HTML
        for p in self.soup.findAll('p'):

            # This flag is used to break out of loops early.  It is set if a
            # double break is detected inside a paragraph.  Once we find one,
            # stop checking that paragraph.
            p_has_error = False

            # Iterate through all of the <br /> in the <p>
            for br in p.findAll('br'):

                # Stop looking if we found an error already
                if p_has_error:
                    break

                # Check the next siblings of the <br /> to see if we can find
                # another <br />, skipping whitespace.
                for next_sibling in br.nextSiblingGenerator():

                    # If next sibling is a tag, and the name is 'br', raise an error
                    if isinstance(next_sibling, Tag) and next_sibling.name == 'br':
                        p_text = truncate_text(self.soup_to_text(p), 32)
                        p_has_error = True
                        yield LowError(self, 'Double breaks found in paragraph beginning with "%s"' % p_text)
                        break
                    # If next sibling is a string, and it is whitespace, keep looking
                    elif isinstance(next_sibling, NavigableString) and not next_sibling.strip():
                        continue
                    # If it's something else, stop looking
                    else:
                        break


# Validates that file(s) inside the product aren't used elsewhere
class DuplicateFileChecksum(ContentCheck):

    title = "File Uniqueness"
    description = "Duplicate files should be avoided."
    action = "Attempt to resolve duplicate files."

    render = True
    sort_order = 6

    def html_list(self, brains):
        li = " ".join(['<li><a href="%s/view">%s</a></li>' % (x.getURL(), x.Title) for x in brains])
        ul = "<ul>%s</ul>" % li
        return ul

    def value(self):

        # Get all items inside this product
        path = '/'.join(self.context.getPhysicalPath())
        results = self.portal_catalog.searchResults({'path' : path})

        # Create a dict of { UID : r }
        return dict([(x.UID, x) for x in results if x.cksum])

    def check(self):

        # Get a dict of { UID : r } for everything in this product that has a
        # cksum indexed
        uid_cksum = self.value()

        # If we have data, look for duplicates
        if uid_cksum.values:

            # grab the individual checksums and uids for items inside this product.
            cksums = [x.cksum for x in uid_cksum.values()]
            uids = uid_cksum.keys()

            # Check for duplicate files within this product
            product_duplicate_cksums = [x for x in set(cksums) if cksums.count(x) > 1]

            if product_duplicate_cksums:
                product_brains = [x for x in uid_cksum.values()
                                  if x.cksum in product_duplicate_cksums]

                ul = self.html_list(product_brains)

                yield LowError(self, 'Duplicate files found inside this product: %s' % ul)

            # Find all items with those checksums
            duplicates = self.portal_catalog.searchResults({'cksum' : cksums})

            # Filter out UIDs inside this product
            duplicates = [x for x in duplicates if x.UID not in uids]

            # If we found duplicate files outside this product
            if duplicates:
                ul = self.html_list(duplicates)
                yield LowError(self, 'Duplicate files found in other products: %s' % ul)