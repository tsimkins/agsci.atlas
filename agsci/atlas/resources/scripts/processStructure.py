import json

data = {}

# Set up the hierarchy of category types
content_types = ['atlas_state_extension_team', 'atlas_program_team', 'curricula']

# Pull that into a containers dict
containers = dict([(x,None) for x in content_types])

for i in sorted(open("extension_structure.txt", "r").readlines()):

    # Ignore blank lines
    if not i.strip():
        continue

    # Ignore comments lines
    if i.strip().startswith('#'):
        continue

    values = i.strip().split('\t')

    for level in range(0, len(values)):

        content_type = content_types[level]

        # Get the human readable name, and make it into a short name
        name = values[level].strip()

        if level == 0:
            container_object = data
        else:
            container_object = containers.get(content_types[level-1], None)


        if container_object.has_key(name):
            item = container_object[name]
        else:
            item = {}
            container_object[name] = item

        containers[content_type] = item

for (k0,v0) in data.iteritems():
    for (k1,v1) in v0.iteritems():
        curricula = v1.keys()
        v0[k1] = curricula

print json.dumps(data, indent=4, sort_keys=True)