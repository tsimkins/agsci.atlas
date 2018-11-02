from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from agsci.atlas.constants import DELIMITER

from .. import ContentCheck, ConditionalCheck
from ..error import LowError

# Validates that the right number of EPAS categories are selected
# Parent class with basic logic
class ProductEPAS(ContentCheck):

    @property
    def error(self):
        return ConditionalCheck(self.context).error

    title = "EPAS Selections (Updated Structure)"
    fields = ('epas_team', 'epas_topic')
    action = "Select the appropriate EPAS information under the 'Categorization' tab."

    @property
    def description(self):
        return '%s products should have one each of Team and Topic selected.' % self.context.Type()

    # Sort order (lower is higher)
    sort_order = 3

    # Maximum number of topics
    max_topics = 1

    # This generates all valid possibilities for counts of topics.
    # The assumption is that (due to the structure of the data) we will never
    # have a larger number at a higher level.
    @property
    def required_values(self):
        v = []

        max_range = self.max_topics + 1

        for i in range(1,max_range):
            for j in range(1,max_range):
                v.append(
                    tuple(
                        sorted([i,j])
                    )
                )

        v = list(set(v))

        return v

    # Number of selections for each field.
    def value(self):
        try:
            return tuple([len(getattr(self.context, x, [])) for x in self.fields])
        except TypeError:
            return (0,0)

    def check(self):
        v = self.value()

        if v not in self.required_values:
            yield self.error(self, u"Number of selections incorrect.")


# Validates that the right number of EPAS categories are selected

class WorkshopGroupEPAS(ProductEPAS):

    max_topics = 3

    @property
    def description(self):
        return '%s products should have at least one (and up to three) Team(s) and Topic(s) selected.' % self.context.Type()


class WebinarGroupEPAS(WorkshopGroupEPAS):

    pass


class OnlineCourseGroupEPAS(ProductEPAS):

    pass


class EPASLevelValidation(ContentCheck):

    child_vocabulary_name = u""

    @property
    def error(self):
        return ConditionalCheck(self.context).error

    # Sort order (lower is higher)
    sort_order = 2

    epas_titles = {
        'epas_team': 'Team',
        'epas_topic': 'Topic',
        'epas_subtopic': 'Subtopic'
    }

    epas_levels = ['epas_team', 'epas_topic']

    @property
    def title(self):
        return "EPAS %s" % self.field_title

    @property
    def field_title(self):
        return self.epas_titles.get(self.epas_levels[-1])

    @property
    def description(self):
        return "%s should be assigned when available." % self.title

    @property
    def action(self):
        return "Under the 'Categorization' tab, select the appropriate %s." % self.title

    def value(self):
        # Get the category level values
        v1 = getattr(self.context, self.epas_levels[0] , [])
        v2 = getattr(self.context, self.epas_levels[1], [])

        # Make these lists if they were None values
        if not v1:
            v1 = []

        if not v2:
            v2 = []

        return (v1, v2)

    # The vocabulary for the second level
    @property
    def vocabulary(self):
        factory = getUtility(IVocabularyFactory, self.child_vocabulary_name)
        return factory(self.context)

    # All potential options for the second level vocabulary
    def options(self):
        try:
            return [x.value for x in self.vocabulary]
        except:
            return []

    def check(self):

        # Get the level 1 and level 2 values
        (v1, v2) = self.value()

        # Iterate through the level 1 values.  If a level 2 value is available
        # for that level 1, but no level 2s are selected, throw an error
        options = self.options()

        for i in v1:

            available_v2 = [x for x in options if x.startswith('%s%s' % (i, DELIMITER))]

            if available_v2:
                if not (set(v2) & set(available_v2)):

                    yield self.error(self, (u"Values for '%s' under %s '%s' are " +
                                           u"available, but not selected.") %
                                              (self.field_title,
                                               self.epas_titles.get(self.epas_levels[0]),
                                               i))

class EPASTeamValidation(EPASLevelValidation):
    child_vocabulary_name = u"agsci.atlas.EPASTopic"

class EPASTopicValidation(EPASLevelValidation):
    child_vocabulary_name = u"agsci.atlas.EPASSubtopic"

    epas_levels = ['epas_topic', 'epas_subtopic']

class EPASPrimaryTeamValidation(ContentCheck):

    title = "EPAS Primary Team (Updated Structure)"

    action = "Select the appropriate EPAS Primary Team information under the 'Categorization' tab."

    description = "Products should have a Primary Team selected for reporting, and this team must be one of the selected Teams."

    # Sort order (lower is higher)
    sort_order = 3

    def value(self):
        return getattr(self.context, 'epas_primary_team', None)

    def check(self):
        v = self.value()

        if not v:
            yield LowError(self, u"No EPAS Primary Team is selected.")

        else:
            epas_team = getattr(self.context, 'epas_team', [])

            if epas_team and isinstance(epas_team, (list, tuple)):
                if v not in epas_team:
                    yield LowError(self, u"EPAS Primary Team is not in selected EPAS Teams.")