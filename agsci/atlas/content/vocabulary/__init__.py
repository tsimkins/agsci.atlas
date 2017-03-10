from Products.CMFCore.utils import getToolByName
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import directlyProvides, implements

from .calculator import AtlasMetadataCalculator, ExtensionMetadataCalculator

from agsci.atlas.content import DELIMITER

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

    preserve_order = False

    items = ['N/A',]

    def __call__(self, context):

        items = list(set(self.items))

        if not self.preserve_order:
            items.sort()

        terms = [SimpleTerm(x,title=x) for x in items]

        return SimpleVocabulary(terms)

class KeyValueVocabulary(object):

    implements(IVocabularyFactory)

    items = [
        ('N/A', 'N/A'),
    ]

    def __call__(self, context):

        return SimpleVocabulary(
            [
                SimpleTerm(x, title=y) for (x, y) in self.items
            ]
        )


# Number of columns in tile folder view

class TileFolderColumnsVocabulary(StaticVocabulary):

    items = ['%d' % x for x in range(1,6)]


class LanguageVocabulary(StaticVocabulary):

    preserve_order = True

    items = [
        'English',
        'Spanish',
        'French',
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

            v = map(lambda x: '%s%s%s' % (program_team, DELIMITER, x), v)

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

class StoreViewIdVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):

        # Hardcoded based on Magento stores.
        return SimpleVocabulary(
            [
                SimpleTerm(2, title='External'),
                SimpleTerm(3, title='Internal'),
            ]
        )

# Used for faceted nav
class PeopleVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):

        portal_catalog = getToolByName(context, 'portal_catalog')

        results = portal_catalog.searchResults({'Type' : 'Person', 'sort_on' : 'sortable_title'})

        return SimpleVocabulary(
            [
                SimpleTerm(x.getId, title=x.Title) for x in results
            ]
        )

class FacetedNavigationSortVocabulary(KeyValueVocabulary):

    items = [
        ('sortable_title', 'Title'),
        ('effective', 'Published Date'),
        ('created', 'Created Date'),
    ]

class ProductStatusVocabulary(KeyValueVocabulary):

    items = [
        ('requires_initial_review', 'Owner Review'),
        ('private', 'Private'),
        ('pending', 'Web Team Review'),
        ('requires_feedback', 'Owner Feedback'),
        ('published', 'Published'),
        ('expired', 'Expired'),
        ('expiring_soon', 'Expiring Soon'),
        ('archive', 'Archived'),
    ]

class PublicationFormatVocabulary(KeyValueVocabulary):

    items = [
        ('hardcopy', 'Hard Copy'),
        ('digital', 'Digital'),
    ]

# US States for locations and people
class StatesVocabulary(KeyValueVocabulary):

    items = [
                ('PA', 'Pennsylvania'),
                ('AL', 'Alabama'),
                ('AK', 'Alaska'),
                ('AS', 'American Samoa'),
                ('AZ', 'Arizona'),
                ('AR', 'Arkansas'),
                ('CA', 'California'),
                ('CO', 'Colorado'),
                ('CT', 'Connecticut'),
                ('DE', 'Delaware'),
                ('DC', 'District of Columbia'),
                ('FL', 'Florida'),
                ('GA', 'Georgia'),
                ('GU', 'Guam'),
                ('HI', 'Hawaii'),
                ('ID', 'Idaho'),
                ('IL', 'Illinois'),
                ('IN', 'Indiana'),
                ('IA', 'Iowa'),
                ('KS', 'Kansas'),
                ('KY', 'Kentucky'),
                ('LA', 'Louisiana'),
                ('ME', 'Maine'),
                ('MH', 'Marshall Islands'),
                ('MD', 'Maryland'),
                ('MA', 'Massachusetts'),
                ('MI', 'Michigan'),
                ('FM', 'Micronesia'),
                ('MN', 'Minnesota'),
                ('MS', 'Mississippi'),
                ('MO', 'Missouri'),
                ('MT', 'Montana'),
                ('NE', 'Nebraska'),
                ('NV', 'Nevada'),
                ('NH', 'New Hampshire'),
                ('NJ', 'New Jersey'),
                ('NM', 'New Mexico'),
                ('NY', 'New York'),
                ('NC', 'North Carolina'),
                ('ND', 'North Dakota'),
                ('MP', 'Northern Marianas'),
                ('OH', 'Ohio'),
                ('OK', 'Oklahoma'),
                ('OR', 'Oregon'),
                ('PW', 'Palau'),
                ('PR', 'Puerto Rico'),
                ('RI', 'Rhode Island'),
                ('SC', 'South Carolina'),
                ('SD', 'South Dakota'),
                ('TN', 'Tennessee'),
                ('TX', 'Texas'),
                ('UT', 'Utah'),
                ('VT', 'Vermont'),
                ('VI', 'Virgin Islands'),
                ('VA', 'Virginia'),
                ('WA', 'Washington'),
                ('WV', 'West Virginia'),
                ('WI', 'Wisconsin'),
                ('WY', 'Wyoming'),
            ]

# Factories
TileFolderColumnsVocabularyFactory = TileFolderColumnsVocabulary()

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

StoreViewIdVocabularyFactory = StoreViewIdVocabulary()

PeopleVocabularyFactory = PeopleVocabulary()
FacetedNavigationSortVocabularyFactory = FacetedNavigationSortVocabulary()
ProductStatusVocabularyFactory = ProductStatusVocabulary()

PublicationFormatVocabularyFactory = PublicationFormatVocabulary()

StatesVocabularyFactory = StatesVocabulary()