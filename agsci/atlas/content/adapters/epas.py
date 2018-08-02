from agsci.atlas.constants import CMS_DOMAIN, DELIMITER
from agsci.atlas.ga import CachedJSONData

from . import BaseAtlasAdapter

# Not GA, but the easiest place to put it
class EPASMapping(CachedJSONData):

    # URL for JSON data
    DATA_URL = u"http://%s/magento/epas-mapping.json" % CMS_DOMAIN

    # Redis cache key
    redis_cachekey = u"EPAS_MAPPING_CACHEKEY"

    # Timeout for cache
    CACHED_DATA_TIMEOUT = 86400 # One day

class EPASDataAdapter(BaseAtlasAdapter):

    old_fields = [
        'state_extension_team', 'program_team', 'curriculum',
    ]

    new_fields = [
        'unit', 'team', 'topic',
    ]

    @property
    def data(self):
        return EPASMapping().data

    @property
    def old_values(self):

        values = []

        for _ in self.old_fields:

            __ = getattr(self.context, 'atlas_%s' % _, [])

            if __:
                values.extend([tuple(x.split(DELIMITER)) for x in __])

        return self.api_view.minimizeStructure(values, self.old_fields)

    def count_matches(self, _1, _2):

        matches = 0

        for _ in self.old_fields:
            v_1 = _1.get(_, '')
            v_2 = _2.get(_, '')

            if v_1 and v_2 and v_1 == v_2:
                matches = matches + 1
            else:
                break

        return matches

    @property
    def mapped_values(self):

        mapping_data = self.data

        matches = []

        for _ in self.old_values:
            for (_old, _new) in mapping_data:
                m = self.count_matches(_, _old)
                if m:
                    matches.append((m, _new))
        if matches:
            max_matches = max([x[0] for x in matches])

            return [x[1] for x in matches if x[0] == max_matches]

        return []

    @property
    def new_values(self):

        data = dict([(x, []) for x in self.new_fields])

        for _ in self.mapped_values:
            for i in range(0, len(self.new_fields)):
                values = [_.get(x, '') for x in self.new_fields[:i+1]]

                # Strip off empty values
                while not values[-1]:
                    values.pop()

                if len(values) == i+1:
                    v = DELIMITER.join(values)
                    k = self.new_fields[i]
                    if v not in data[k]:
                        data[k].append(v)

        return data