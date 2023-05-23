import json

data = {}

# Set up the hierarchy of category types
content_types = ['atlas_category_level_1', 'atlas_category_level_2', 'atlas_category_level_3']

# Pull that into a containers dict
containers = dict([(x,None) for x in content_types])

for i in open("ia.txt", "r").readlines():

    # Initialize filter_sets
    filter_sets = None

    # Ignore blank lines
    if not i.strip():
        continue

    # Ignore comments lines
    if i.strip().startswith('#'):
        continue

    # Get the level (1,2,3) and content_type based on the number of tabs
    level = i.count('\t')
    content_type = content_types[level]

    # Get the human readable name, and make it into a short name
    name = i.strip()

    # If the name contains filter_sets, split it out into the names and filters
    # Split the filters on ;
    if '|' in name:
        (name, filter_sets) = name.split('|')
        filter_sets = map(lambda x: x.strip(), filter_sets.split(';'))


    if level == 0:
        container_object = data
    else:
        container_object = containers.get(content_types[level-1], None)

    if name in container_object:
        item = container_object[name]

    else:
        if filter_sets:
            item = list(filter_sets)
        else:
            item = {}
        container_object[name] = item

    containers[content_type] = item

print json.dumps(data, indent=4, sort_keys=True)
