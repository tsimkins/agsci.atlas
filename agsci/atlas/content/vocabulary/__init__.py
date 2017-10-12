from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from zope.component import getUtility, getUtilitiesFor
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import implements

from .calculator import AtlasMetadataCalculator, ExtensionMetadataCalculator

from agsci.atlas.constants import DELIMITER

class IRegistryVocabularyFactory(IVocabularyFactory):
    pass

class BaseVocabulary(object):

    implements(IVocabularyFactory)

class MetadataVocabulary(BaseVocabulary):

    content_type = None

    metadata_calculator = AtlasMetadataCalculator

    def __call__(self, context):
        mc = self.metadata_calculator(self.content_type)
        return mc.getTermsForType()

class CategoryLevel1Vocabulary(MetadataVocabulary):
    content_type = 'CategoryLevel1'

class CategoryLevel2Vocabulary(MetadataVocabulary):
    content_type = 'CategoryLevel2'

class CategoryLevel3Vocabulary(MetadataVocabulary):
    content_type = 'CategoryLevel3'

class StateExtensionTeamVocabulary(MetadataVocabulary):
    content_type = 'StateExtensionTeam'

    metadata_calculator = ExtensionMetadataCalculator

class ProgramTeamVocabulary(StateExtensionTeamVocabulary):
    content_type = 'ProgramTeam'

class StaticVocabulary(BaseVocabulary):

    preserve_order = False

    items = ['N/A',]

    def __call__(self, context):

        unsorted_items = self.items

        items = list(set(unsorted_items))

        def sort_key(x):
            return unsorted_items.index(x)

        if self.preserve_order:
            items.sort(key=sort_key)
        else:
            items.sort()

        terms = [SimpleTerm(x, title=x) for x in items]

        return SimpleVocabulary(terms)

class RegistryVocabulary(StaticVocabulary):

    __doc__ = u"Registry Vocabulary"

    defaults = ('N/A',)

    @property
    def registry_key(self):
        for (name, vocab) in getUtilitiesFor(IVocabularyFactory):
            if type(vocab) == type(self):
                return name

    @property
    def items(self):

        registry_key = self.registry_key

        if registry_key:

            registry = getUtility(IRegistry)

            v = registry.get(registry_key)

            if isinstance(v, (list, tuple)):
                return v

        return []

class KeyValueVocabulary(BaseVocabulary):

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

    items = ['%d' % x for x in range(1, 6)]


class LanguageVocabulary(RegistryVocabulary):

    __doc__ = u"Languages for products"

    preserve_order = True

    defaults = (
        u'English',
        u'Spanish',
        u'French',
    )


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

# Existing counties, plus custom options for people who are not county-based.
class PersonCountyVocabulary(CountyVocabulary):

    preserve_order = True

    @property
    def items(self):
        _ = super(PersonCountyVocabulary, self).items

        _.sort()

        _.extend([
            "University Park",
        ])

        return _

class CventEventTypeVocabulary(StaticVocabulary):

    items = [
        u'Workshop',
        u'Conference',
        u'Webinar',
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
        u'Continuing Education Unit (CEU)',
        u'Private Applicator',
    ]

class CreditCategoryVocabulary(StaticVocabulary):

    items = [
        u'Certification',
        u'License',
        u'Professional Education',
        u'Core Credits',
        u'01 Agronomic Crops',
        u'02 Fruit and Nuts',
        u'03 Vegetable Crops',
        u'04 Agricultural Animals',
        u'05 Forest Pest Control',
        u'06 Ornamental and Shade Trees',
        u'07 Lawn and Turf',
        u'08 Seed Treatment',
        u'09 Aquatic Pest Control',
        u'10 Right-of-way and Weeds',
        u'11 Household and Health Related',
        u'12 Wood Destroying Pests',
        u'13 Structural Fumigation',
        u'15 Public Health - Vertebrate Pests',
        u'16 Public Health - Invertebrate Pests',
        u'17 Regulatory Pest Control',
        u'18 Demonstration and Research',
        u'19 Wood Preservation',
        u'20 Commodity and Space Fumigation',
        u'21 Soil Fumigation',
        u'22 Interior Plantscape',
        u'23 Park or School Pest Control',
        u'24 Swimming Pools',
        u'25 Aerial Applicator',
        u'26 Sewer Root Control'
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
        ('private', 'Private'),
        ('pending', 'Web Team Review'),
        ('requires_feedback', 'Owner Feedback'),
        ('published', 'Published'),
        ('expired', 'Expired'),
        ('expiring_soon', 'Expiring Soon'),
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

# Webinar Recording File Types
class WebinarRecordingFileTypesVocabulary(StaticVocabulary):

    preserve_order = True

    items = [
        u'Presentation',
        u'Handout',
    ]

# "Hot Topics" for Homepage.  Maintained in registry, since these will be
# updated
class HomepageTopicsVocabulary(RegistryVocabulary):

    __doc__ = u"Homepage Topics"

    defaults = (
        u'Avian Influenza',
        u'Ag Alternatives',
        u"Let's Preserve",
    )


class EducationalDriversVocabulary(RegistryVocabulary, CategoryLevel2Vocabulary):

    __doc__ = u"Educational Drivers"

    defaults = (
        u'Optimize Your Business',
        u'Getting Started',
        u'Keep Up With Regulations',
        u'Common Problems',
        u'Latest Research',
        u'Market Trends',
    )

    def __call__(self, context):

        items = []

        l2 = super(CategoryLevel2Vocabulary, self).__call__(context)

        for i in l2.by_value.keys():
            for j in self.items:
                items.append(DELIMITER.join([i, j]))

        terms = [SimpleTerm(x, title=x) for x in sorted(items)]

        return SimpleVocabulary(terms)

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
PersonCountyVocabularyFactory = PersonCountyVocabulary()

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

WebinarRecordingFileTypesVocabularyFactory = WebinarRecordingFileTypesVocabulary()

HomepageTopicsVocabularyFactory = HomepageTopicsVocabulary()

EducationalDriversVocabularyFactory = EducationalDriversVocabulary()