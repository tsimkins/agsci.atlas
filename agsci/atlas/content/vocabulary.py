from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from Products.CMFCore.utils import getToolByName
from zope.interface import directlyProvides
from zope.interface import implements
from agsci.atlas.content import getMetadataByContentType, required_metadata_content_types

def getTermsForType(context, content_type):

    portal_catalog = getToolByName(context, "portal_catalog")

    terms = []
    
    if content_type not in required_metadata_content_types:
        terms.append(
            SimpleTerm('',title='N/A')
        )

    results = portal_catalog.searchResults({'Type' : content_type})
    
    for r in results:
        o = r.getObject()
        v = getMetadataByContentType(o, content_type)
        if v:
            terms.append(SimpleTerm(v,title=v))

    return SimpleVocabulary(terms)


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

class SubtopicVocabulary(BaseVocabulary):
    content_type = 'Subtopic'

CategoryVocabularyFactory = CategoryVocabulary()
ProgramVocabularyFactory = ProgramVocabulary()
TopicVocabularyFactory = TopicVocabulary()
SubtopicVocabularyFactory = SubtopicVocabulary()