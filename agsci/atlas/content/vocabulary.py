from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from Products.CMFCore.utils import getToolByName
from zope.interface import directlyProvides
from zope.interface import implements
from agsci.atlas.content import getMetadataByContentType, required_metadata_content_types

def getTermsForType(context, content_type):

    portal_catalog = getToolByName(context, "portal_catalog")

    results = portal_catalog.searchResults({'Type' : content_type})
    
    terms = []
    
    for r in results:
        o = r.getObject()
        v = getMetadataByContentType(o, content_type)
        if v:
            magento_id = getattr(o, 'magento_id', None)
            if magento_id:
                terms.append((magento_id, v))

    terms.sort(key=lambda x:x[1])

    return SimpleVocabulary([SimpleTerm(x[0],title=x[1]) for x in terms])


class BaseVocabulary(object):

    implements(IVocabularyFactory)

    content_type = None

    def __call__(self, context):
        return getTermsForType(context, self.content_type)

class CategoryVocabulary(BaseVocabulary):
    content_type = 'Category'

class ProgramVocabulary(BaseVocabulary):
    content_type = 'Program'

class TopicVocabulary(BaseVocabulary):
    content_type = 'Topic'

class StaticVocabulary(object):

    implements(IVocabularyFactory)

    items = ['N/A',]

    def __call__(self, context):

        terms = [SimpleTerm(x,title=x) for x in self.items]
    
        return SimpleVocabulary(terms)

class FiltersVocabulary(StaticVocabulary):

    items = [
        'Agronomic Crop',
        'Business Topic',
        'Cover Crop',
        'Disaster',
        'Energy Source',
        'Farm Equipment/Structure',
        'Forage Crop',
        'Fruit',
        'Home/Commercial',
        'Industry',
        'Plant Type',
        'Turfgrass/Lawn',
        'Vegetable',
        'Water Source'
    ]

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


CategoryVocabularyFactory = CategoryVocabulary()
ProgramVocabularyFactory = ProgramVocabulary()
TopicVocabularyFactory = TopicVocabulary()
FiltersVocabularyFactory = FiltersVocabulary()
LanguageVocabularyFactory = LanguageVocabulary()
HomeOrCommercialVocabularyFactory = HomeOrCommercialVocabulary()