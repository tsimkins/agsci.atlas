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
            raise ValueError("%s not a valid metadata content type for this class.")

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

    def getObjectsForType(self):

        results = self.portal_catalog.searchResults({'Type' : self.content_type})

        return map(lambda x: x.getObject(), results)

    def getTermsForType(self):

        terms = []

        for o in self.getObjectsForType():

            v = self.getMetadataForObject(o)

            if v:
                terms.append((v, v))

        terms.sort(key=lambda x:x[1])

        return SimpleVocabulary([SimpleTerm(x[0],title=x[1]) for x in terms])


class ExtensionMetadataCalculator(AtlasMetadataCalculator):

    metadata_content_types = ['StateExtensionTeam', 'ProgramTeam']


class AtlasFilterCalculator(object):

    content_types_with_filters = {'CategoryLevel3' : 'atlas_category_level_3',}

    @property
    def portal_catalog(self):
        return getToolByName(getSite(), "portal_catalog")

    # Get a list of unique filter set brains, optionally filtered by a list of
    # names
    def getFilterSets(self, names=[]):

        query = {'Type' : 'FilterSet'}

        if names:
            query['Title'] = names

        return self.portal_catalog.searchResults(query)

    # Get a list of filter set name strings
    def getFilterSetNames(self, names=[]):
        return sorted(map(lambda x: x.Title, self.getFilterSets(names)))

    # Get a dict of FilterSet name to individual filter values for all filter sets
    def getFilterSetDict(self, names=[]):

        filter_sets = map(lambda x: x.getObject(), self.getFilterSets(names))

        data = dict(map(lambda x: (x.Title(), getattr(x, 'atlas_filters', [])), filter_sets))

        return data

    # Get a dict of ':' delimited category name to the individual filters for the
    # filter sets configured for that category
    def getFilterDictForCategory(self, content_type):

        data = {}

        # Filter set name to individual filters
        filter_set_data = self.getFilterSetDict()

        # Metadata calculator for category content type
        mc = AtlasMetadataCalculator(content_type)

        # Iterate through all category objects of that type
        objects = mc.getObjectsForType()

        for o in objects:

            # Get filter sets for this particular category object
            filter_sets = getattr(o, 'atlas_filter_sets', [])

            if filter_sets:
                # Get the ':' delimited metadata for the category so we can look
                # up the individual filters
                metadata = mc.getMetadataForObject(o)

                if metadata:

                    # Create an entry for this category in the dict if it doesn't
                    # already exist
                    if not data.has_key(metadata):
                        data[metadata] = []

                    # Iterate through the filter sets for this particular category
                    # and add the individual filters to the list of filters for
                    # this category.
                    for i in filter_sets:
                        data[metadata].extend(filter_set_data.get(i, []))

        return data

    # Given an object (e.g. an Article), return a sorted list of individual filters
    # that can be applied to that object.
    def getFiltersForObject(self, context):

        # List to hold all of the potential filters for this object.
        data = []

        # Iterate through the dict (at the class level) of the content types that
        # can have filters applied
        for (content_type, category_field) in self.content_types_with_filters.iteritems():

            # Get the dict of ':' delimited category name to the individual 
            # filters for this level of category
            filter_data = self.getFilterDictForCategory(content_type)

            # Get the categories that are selected for this object
            context_categories = getattr(context, category_field, [])

            # If there are no categories selected(e.g. on create) use the default
            if not context_categories:
                context_categories = defaultMetadataFactory(context, 'CategoryLevel3')

            # Iterate through those categories that are selected, and add the 
            # individual filters to the list
            if context_categories:
                for i in context_categories:
                    data.extend(filter_data.get(i, []))

        # Make the list unique
        data = list(set(data))

        # Return the sorted unique list
        return sorted(data)