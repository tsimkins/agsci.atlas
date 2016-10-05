from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.component.hooks import getSite

# Given an object and the content_type (Category level), return the default value
# for that metadata.  I.e. "Give me the default CategoryLevel3 for this object.'
def defaultMetadataFactory(context, content_type):

    mc = AtlasMetadataCalculator(content_type)

    v = mc.getMetadataForObject(context)

    if v:
        return [v]

    return v

# Class to return ':' delimited list of hierarchical Atlas metadata for each
# level of hierarchy.

class AtlasMetadataCalculator(object):

    # Sequence of content types in hierarchy
    metadata_content_types = ['CategoryLevel1', 'CategoryLevel2', 'CategoryLevel3']

    def __init__(self, content_type):

        if content_type not in self.metadata_content_types:
            raise ValueError("%s not a valid metadata content type for this class." % content_type)

        self.content_type = content_type

    @property
    def portal_catalog(self):
        return getToolByName(getSite(), "portal_catalog")

    def getMetadataForObject(self, context):

        filtered_metadata_content_types = self.metadata_content_types[0:self.metadata_content_types.index(self.content_type)+1]

        v = {}

        for o in context.aq_chain:

            if IPloneSiteRoot.providedBy(o):
                break

            if hasattr(o, 'Type') and hasattr(o.Type, '__call__'):
                if o.Type() in self.metadata_content_types:
                    v[o.Type()] = o.Title()
            else:
                break

        if v.has_key(self.content_type):
            return ':'.join([v.get(x) for x in filtered_metadata_content_types if v.has_key(x)])

        return None

    def getObjectsForType(self, value=None):

        query = {'Type' : self.content_type}

        if value:
            query[self.content_type] = value

        results = self.portal_catalog.searchResults(query)

        return map(lambda x: x.getObject(), results)

    def getTermsForType(self):

        terms = []

        for o in self.getObjectsForType():

            v = self.getMetadataForObject(o)

            if v:
                terms.append((v, v))

        terms = list(set(terms))

        terms.sort(key=lambda x:x[1])

        return SimpleVocabulary([SimpleTerm(x[0],title=x[1]) for x in terms])


class ExtensionMetadataCalculator(AtlasMetadataCalculator):

    metadata_content_types = ['StateExtensionTeam', 'ProgramTeam']