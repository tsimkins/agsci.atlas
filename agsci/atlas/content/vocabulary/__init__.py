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

        terms = [SimpleTerm(x,title=x) for x in self.items]
    
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


CategoryLevel1VocabularyFactory = CategoryLevel1Vocabulary()
CategoryLevel2VocabularyFactory = CategoryLevel2Vocabulary()
CategoryLevel3VocabularyFactory = CategoryLevel3Vocabulary()
LanguageVocabularyFactory = LanguageVocabulary()
SkillLevelVocabularyFactory = SkillLevelVocabulary()
