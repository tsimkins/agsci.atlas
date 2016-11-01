
class ProductTypeChecks(object):

    def __init__(self, product_type='', checks=[]):
        self.product_type = product_type
        self.checks = checks

class ContentStructure(object):

    sort_order = {
        'review_state' : ['imported', 'requires_initial_review', 'private',
                          'pending', 'published', 'expiring-soon', 'expired'],
        'Type' : ['Article', 'Publication'],
    }

    def __init__(self, context, results, keys):
        self.context = context
        self.results = results
        self.keys = keys

    @property
    def key_1(self):
        return self.keys[0]

    @property
    def key_2(self):
        try:
            return self.keys[1]
        except IndexError:
            return None

    def getSortOrder(self, x):

        sort_order = self.sort_order.get(self.key_1, [])

        if not sort_order:
            return x.get(self.key_1)

        try:
            return sort_order.index(x.get(self.key_1, ''))
        except ValueError:
            return 99999

    def __call__(self):

        data = {}

        for r in self.results:

            k = getattr(r, self.key_1, None)

            if not k:
                continue

            if not isinstance(k, (list, tuple)):
                k = [k,]

            for _k in k:

                if not data.has_key(_k):
                    data[_k] = {self.key_1 : _k, 'brains' : []}

                data[_k]['brains'].append(r)


        if self.key_2:
            for k in data.keys():
                data[k]['brains'].sort(key=lambda x: getattr(x, self.key_2, ''))

        return sorted(data.values(), key=self.getSortOrder)