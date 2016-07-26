from zope.interface import Interface
from error import HighError, MediumError, LowError

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

    title = "Title Length"
    description = "Titles should be no more than 60 characters."

    def value(self):
        return len(self.context.title)

    def check(self):
        v = self.value()

        if v > 128:
            return HighError(self, "%d characters is too long." % v)
        elif v > 60:
            return MediumError(self, "%d characters is too long." % v)
        elif v < 16:
            return LowError(self, "%d characters may be too short." % v)

        return None


# Validates the product description length
class DescriptionLength(ContentCheck):

    title = "Description Length"
    description = "Descriptions should be no more than 160 characters."

    def value(self):
        return len(self.context.description)

    def check(self):

        v = self.value()

        if v > 255:
            return HighError(self, "%d characters is too long." % v)
        elif v > 160:
            return MediumError(self, "%d characters is too long." % v)
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
        return tuple([len(getattr(self.context, x, [])) for x in self.fields])

    def check(self):
        v = self.value()
        
        if v != (1,1,1):
            return HighError(self, "Selections incorrect.")
        
        return None
    