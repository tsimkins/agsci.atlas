from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import directlyProvides, implements

from .calculator import AtlasMetadataCalculator, ExtensionMetadataCalculator

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

        items = sorted(list(set(self.items)))

        terms = [SimpleTerm(x,title=x) for x in items]
    
        return SimpleVocabulary(terms)

class LanguageVocabulary(StaticVocabulary):

    items = [
        'English',
        'Spanish',
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

class VideoProvidersVocabulary(StaticVocabulary):

    items = [
                u'YouTube', 
                u'Vimeo',
            ]

class VideoAspectRatioVocabulary(StaticVocabulary):

    items = [
                u'16:9',
                u'3:2',
                u'4:3',
            ]

class CreditTypeVocabulary(StaticVocabulary):

    items = [
                u'Credit Type 1',
                u'Credit Type 2',
                u'Credit Type 3',
            ]

class CreditCategoryVocabulary(StaticVocabulary):

    items = [
                u'Credit Category 1',
                u'Credit Category 2',
                u'Credit Category 3',
            ]

CategoryLevel1VocabularyFactory = CategoryLevel1Vocabulary()
CategoryLevel2VocabularyFactory = CategoryLevel2Vocabulary()
CategoryLevel3VocabularyFactory = CategoryLevel3Vocabulary()

StateExtensionTeamVocabularyFactory = StateExtensionTeamVocabulary()
ProgramTeamVocabularyFactory = ProgramTeamVocabulary()
CurriculumVocabularyFactory = CurriculumVocabulary()

LanguageVocabularyFactory = LanguageVocabulary()
SkillLevelVocabularyFactory = SkillLevelVocabulary()
CountyVocabularyFactory = CountyVocabulary()

CventEventTypeVocabularyFactory = CventEventTypeVocabulary()

VideoProvidersVocabularyFactory = VideoProvidersVocabulary()
VideoAspectRatioVocabularyFactory = VideoAspectRatioVocabulary()

CreditTypeVocabularyFactory = CreditTypeVocabulary()
CreditCategoryVocabularyFactory = CreditCategoryVocabulary()