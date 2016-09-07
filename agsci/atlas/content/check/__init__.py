from BeautifulSoup import BeautifulSoup
from Products.CMFCore.utils import getToolByName
from zope.component import subscribers
from zope.interface import Interface
from error import HighError, MediumError, LowError
from zope.globalrequest import getRequest
from zope.annotation.interfaces import IAnnotations
from ..vocabulary.calculator import AtlasMetadataCalculator

# Cache errors on HTTP Request, since we may be calling this multiple times.
# Ref: http://docs.plone.org/manage/deploying/performance/decorators.html#id7
def getValidationErrors(context):

    request = getRequest()

    key = "product-validation-errors"

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
        c = i.check()

        if c:
            errors.append(c)

    errors.sort(key=lambda x: levels.index(x.level))

    return errors

# Interface for warning subscribers
class IContentCheck(Interface):
    pass

# Base class for content check
class ContentCheck(object):

    # Title for the check
    title = "Default Check"

    # Description for the check
    description = ""

    def __init__(self, context):
        self.context = context

    def value(self):
        """ Returns the value of the attribute being checked """

    def check(self):
        """ Performs the check and returns HighError/MediumError/LowError/None """


# Validates the product title length
class TitleLength(ContentCheck):

    title = "Product Title Length"
    description = "Titles should be no more than 60 characters."

    def value(self):
        return len(self.context.title)

    def check(self):
        v = self.value()

        if v > 128:
            return HighError(self, "%d characters is too long." % v)
        elif v > 80:
            return MediumError(self, "%d characters is too long." % v)
        elif v > 60:
            return LowError(self, "%d characters is too long." % v)
        elif v < 16:
            return LowError(self, "%d characters may be too short." % v)

        return None


# Validates the product description length
class DescriptionLength(ContentCheck):

    title = "Product Description Length"
    description = "Product must have a description, which should be a maximum of 160 characters."

    def value(self):
        return len(self.context.description)

    def check(self):

        v = self.value()

        if v > 255:
            return HighError(self, "%d characters is too long." % v)
        elif v > 200:
            return MediumError(self, "%d characters is too long." % v)
        elif v > 160:
            return LowError(self, "%d characters is too long." % v)
        elif v == 0:
            return HighError(self, "A description is required for this product.")
        elif v < 32:
            return LowError(self, "%d characters may be too short." % v)

        return None

# Validates that the right number of EPAS categories are selected
# Parent class with basic logic
class ProductEPAS(ContentCheck):

    title = "EPAS Selections"
    fields = ('atlas_state_extension_team', 'atlas_program_team', 'atlas_curriculum')

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
            return HighError(self, "Selections incorrect.")

        return None


# Validates that the right number of EPAS categories are selected
class ArticleEPAS(ProductEPAS):

    description = "Articles should have one each of State Extension Team, Program Team, and Curriculum selected."

class VideoEPAS(ProductEPAS):

    description = "Videos should have one each of State Extension Team, Program Team, and Curriculum selected."


class ProductCategoryValidation(ContentCheck):

    category_fields = [1, 2]

    @property
    def title(self):
        return "Category Level %d" % self.category_fields[-1]

    @property
    def description(self):
        return "%s should be assigned when available." % self.title

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

                    return HighError(self, ("Values for Category Level %d '%s' " +
                                     "are available, but not selected. Best practice " +
                                     "is to select all levels of categories where " +
                                     "options are available.") % (self.category_fields[1], i))

        return None

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
            return HighError(self, "Category Level 1 must be assigned.")
        return None


# Validates that a Category Level 2 is selected for all Category Level 1's
# that are available.
class ProductCategory2(ProductCategoryValidation):

    pass

# Validates that a Category Level 3 is selected for all Category Level 2's
# that are available.
class ProductCategory3(ProductCategoryValidation):

    category_fields = [2, 3]

# Trigger for Demo.  Trigger this by adding "demo_error" to the title
class DemoTrigger(ContentCheck):

    title = "Demo Error Title"
    description = "Demo Error Description"

    def value(self):
        return self.context.title

    def check(self):
        if 'demo_error' in self.value().lower():
            return HighError(self, "You can't have that in the title!")

        return None

# Checks for issues in the text.  This doesn't actually check, but is a parent
# class for other checks.
class BodyTextCheck(ContentCheck):

    # Title for the check
    title = "Body Text Check"

    # Description for the check
    description = ""

    @property
    def contents(self):
        if hasattr(self.context, 'getPages'):
            return self.context.getPages()

        return []

    def getText(self, o):
        if hasattr(o, 'text') and hasattr(o.text, 'raw'):
            return o.text.raw
        
        return ''

    def value(self):
        v = [
            self.getText(self.context)
        ]
        
        for o in self.contents:
            v.append(self.getText(o))

        return ' '.join(v)

    def soup(self):
        return BeautifulSoup(self.value())

    def check(self):
        pass

# Checks for appropriate heading level hierarchy, e.g. h2 -> h3 -> h4
class HeadingLevels(BodyTextCheck):

    # Title for the check
    title = "HTML: Heading Levels"

    # Description for the check
    description = "Validates that the heading level hierarchy is correct."

    # h1 - h6
    all_heading_tags = ['h%d' % x for x in range(1,7)]

    # Get heading tag objects
    def getHeadingTags(self):
       return self.soup().findAll(self.all_heading_tags)

    def check(self):

        headings = self.getHeadingTags()

        # Get heading tag object names (e.g. 'h2')
        heading_tags = [x.name for x in headings]

        # If no heading tags to check, return
        if not heading_tags:
            return None

        # Check if we have an h1 (not permitted)
        if 'h1' in heading_tags:
            return MediumError(self, "An <h1> heading is not permitted in the body text.")

        # Validate that the first tag in the listing is an h2
        if heading_tags[0] != 'h2':
            return MediumError(self, "The first heading in the body text must be an <h2>.")

        # Check for heading tag order, and ensure we don't skip any
        for i in range(0, len(heading_tags)-1):
            this_heading = heading_tags[i]
            next_heading = heading_tags[i+1]

            this_heading_idx = self.all_heading_tags.index(this_heading)
            next_heading_idx = self.all_heading_tags.index(next_heading)

            if next_heading_idx > this_heading_idx and next_heading_idx != this_heading_idx + 1:
                heading_tag_string = "<%s> to <%s>" % (this_heading, next_heading) # For error message
                return MediumError(self, "Heading levels in the body text are skipped or out of order: %s" % heading_tag_string)

# Check for heading length
class HeadingLength(HeadingLevels):

    # Title for the check
    title = "HTML: Heading Text Length"

    # Description for the check
    description = "Validates that the heading text is not too long. Headings should be a maximum of 120 characters, and ideally 60 characters or less."

    def check(self):
        headings = self.getHeadingTags()

        portal_transforms = getToolByName(self.context, 'portal_transforms')

        for i in headings:
            html = repr(i)
            text = portal_transforms.convert('html_to_text', html).getData()
            text = " ".join(text.strip().split())

            v = len(text)

            if v > 200:
                return HighError(self, "Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > 120:
                return MediumError(self, "Length of %d characters for <%s> heading '%s' is too long." % (v, i.name, text))
            elif v > 60:
                return LowError(self, "Length of %d characters for <%s> heading '%s' may be too long." % (v, i.name, text))