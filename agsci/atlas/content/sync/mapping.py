# These methods map the old Extension Programs/Topics to the new 3-category system
# This is intended to be used on importing content.

from ..vocabulary import CategoryLevel1VocabularyFactory, CategoryLevel2VocabularyFactory, CategoryLevel3VocabularyFactory

category_levels = [CategoryLevel1VocabularyFactory, CategoryLevel2VocabularyFactory, CategoryLevel3VocabularyFactory]

factory_by_type = dict([(x.content_type, x) for x in category_levels])

def fieldToContentType(v):
    return dict([('atlas_category_level_%d' %x, 'CategoryLevel%d' %x) for x in range(1,4)]).get(v, '') 

def getVocabularyValues(context, vocabulary_type):
    v = factory_by_type.get(vocabulary_type)
    return [x.value for x in v(context)._terms]

# Returns a list of mapping 
# ['atlas_category_level_1', 'atlas_category_level_2', 'atlas_category_level_3']
# to each Program and Topic in the old Extension site.

def getMapping(context):

    # Traverse to the .txt static mapping
    resource = context.restrictedTraverse('++resource++agsci.atlas/category-mapping.txt')

    # Get the tsv contents
    tsv = resource.GET()

    # Pull the tsv into a data structure (list of tuples)
    tsv_table = [x.strip().split('\t') for x in tsv.split('\r')]
    tsv_table = [(x[0], x[1:]) for x in tsv_table]
    
    # Pull tuples into a dict where the key is the input, and the value is 
    # atlas_category_level_1..3
    #
    # This step is necessary because one input can have multiple outputs, and
    # that is represented by multiple lines in the tsv file.
    data = {}
    
    for (i,j) in tsv_table:

        if not data.get(i):
            data[i] = []

        data[i].append(j)

    return data

# Given a single or list of programs and topics (mixed), returns a dict with keys of
# atlas_category_level_1..3 and values of a list of the categories at that level.
# This matches the category fields on the behavior
def mapCategories(context, v):

    # If we're passed a string, listify it
    if isinstance(v, (str, unicode)):
        v = [v,]

    # Get the static mapping
    mapping = getMapping(context)
    
    # Initialize dict
    data = {
        'atlas_category_level_1' : [],
        'atlas_category_level_2' : [],
        'atlas_category_level_3' : [],
    }
    
    # Loop through input values
    for i in v:
        # Get the category 1/2/3 for the value
        for j in mapping.get(i):
            # Push those values into the dict at the appropriate level
            for k in range(0,len(j)):
                data['atlas_category_level_%d' % (k+1)].append(j[k])

    # Uniquify the values, and validate the new values against the vocabulary
    for k in data.keys():
        valid_values = getVocabularyValues(context, fieldToContentType(k))
        data[k] = list( set(data[k]) & set(valid_values) ) 

    return data
