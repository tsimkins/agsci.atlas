from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import directlyProvides, implements
from .calculator import AtlasMetadataCalculator, ExtensionMetadataCalculator, AtlasFilterCalculator

class BaseVocabulary(object):

    implements(IVocabularyFactory)

    content_type = None
    
    metadata_calculator = AtlasMetadataCalculator

    def __call__(self, context):
        mc = self.metadata_calculator(self.content_type)
        return mc.getTermsForType()

class CategoryLevel1Vocabulary(BaseVocabulary):
    content_type = 'CategoryLevel1'

class CategoryLevel2Vocabulary(BaseVocabulary):
    content_type = 'CategoryLevel2'

class CategoryLevel3Vocabulary(BaseVocabulary):
    content_type = 'CategoryLevel3'

class StateExtensionTeamVocabulary(BaseVocabulary):
    content_type = 'StateExtensionTeam'
    
    metadata_calculator = ExtensionMetadataCalculator

class ProgramTeamVocabulary(StateExtensionTeamVocabulary):
    content_type = 'ProgramTeam'

class StaticVocabulary(object):

    implements(IVocabularyFactory)

    items = ['N/A',]

    def __call__(self, context):

        terms = [SimpleTerm(x,title=x) for x in self.items]
    
        return SimpleVocabulary(terms)

class LanguageVocabulary(StaticVocabulary):

    items = [
        'English',
        'Spanish',
    ]

class HomeOrCommercialVocabulary(StaticVocabulary):

    items = [
        'Home',
        'Commercial',
    ]

class SkillLevelVocabulary(StaticVocabulary):

    items = [
        'Beginner',
        'Intermediate',
        'Advanced',
    ]

class CurriculumVocabulary(StaticVocabulary):

    @property
    def items(self):

        data = []

        mc = ExtensionMetadataCalculator('ProgramTeam')
        
        for o in mc.getObjectsForType():

            program_team = mc.getMetadataForObject(o)
                        
            v = getattr(o, 'atlas_curriculum', [])
            
            v = map(lambda x: '%s:%s' % (program_team, x), v)
            
            data.extend(v)
        
        return sorted(data)

class FilterSetVocabulary(StaticVocabulary):

    @property
    def items(self):

        mc = AtlasFilterCalculator()
        
        return mc.getFilterSetNames()


class FilterVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):

        mc = AtlasFilterCalculator()
        
        items = mc.getFiltersForObject(context)

        terms = [SimpleTerm(x,title=x) for x in items]

        return SimpleVocabulary(terms)


class CountyVocabulary(StaticVocabulary):

    items = ['Adams', 'Allegheny', 'Armstrong', 'Beaver', 'Bedford',
             'Berks', 'Blair', 'Bradford', 'Bucks', 'Butler', 'Cambria', 'Cameron',
             'Carbon', 'Centre', 'Chester', 'Clarion', 'Clearfield', 'Clinton',
             'Columbia', 'Crawford', 'Cumberland', 'Dauphin', 'Delaware', 'Elk',
             'Erie', 'Fayette', 'Forest', 'Franklin', 'Fulton', 'Greene',
             'Huntingdon', 'Indiana', 'Jefferson', 'Juniata', 'Lackawanna',
             'Lancaster', 'Lawrence', 'Lebanon', 'Lehigh', 'Luzerne', 'Lycoming',
             'McKean', 'Mercer', 'Mifflin', 'Monroe', 'Montgomery', 'Montour',
             'Northampton', 'Northumberland', 'Perry', 'Philadelphia', 'Pike',
             'Potter', 'Schuylkill', 'Snyder', 'Somerset', 'Sullivan', 'Susquehanna',
             'Tioga', 'Union', 'Venango', 'Warren', 'Washington', 'Wayne',
             'Westmoreland', 'Wyoming', 'York']

class CventEventTypeVocabulary(StaticVocabulary):

    items = [
        'Workshop',
        'Conference',
        'Webinar',
    ]

CategoryLevel1VocabularyFactory = CategoryLevel1Vocabulary()
CategoryLevel2VocabularyFactory = CategoryLevel2Vocabulary()
CategoryLevel3VocabularyFactory = CategoryLevel3Vocabulary()

StateExtensionTeamVocabularyFactory = StateExtensionTeamVocabulary()
ProgramTeamVocabularyFactory = ProgramTeamVocabulary()
CurriculumVocabularyFactory = CurriculumVocabulary()

FilterSetVocabularyFactory = FilterSetVocabulary()
FilterVocabularyFactory = FilterVocabulary()

LanguageVocabularyFactory = LanguageVocabulary()
HomeOrCommercialVocabularyFactory = HomeOrCommercialVocabulary()
SkillLevelVocabularyFactory = SkillLevelVocabulary()
CountyVocabularyFactory = CountyVocabulary()

CventEventTypeVocabularyFactory = CventEventTypeVocabulary()
