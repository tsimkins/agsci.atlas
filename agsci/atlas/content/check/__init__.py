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
    description = "Descriptions should be no more than 160 characters."

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
        elif v < 32:
            return LowError(self, "%d characters may be too short." % v)

        return None

# Validates that the right number of EPAS categories are selected
class ArticleEPAS(ContentCheck):

    title = "EPAS Selections"
    description = "Articles should have one each of State Extension Team, Program Team, and Curriculum selected."

    fields = ('atlas_state_extension_team', 'atlas_program_team', 'atlas_curriculum')

    def value(self):
        # Should be (1,1,1)
        try:
            return tuple([len(getattr(self.context, x, [])) for x in self.fields])
        except TypeError:
            return (0,0,0)

    def check(self):
        v = self.value()

        if v != (1,1,1):
            return HighError(self, "Selections incorrect.")

        return None

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
                                     "is to select all levels of categories where" +
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