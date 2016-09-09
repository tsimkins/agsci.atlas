from plone.memoize.instance import memoize

class ProductTypeChecks(object):

    def __init__(self, product_type='', checks=[]):
        self.product_type = product_type
        self.checks = checks


class ContentByReviewState(object):

    sort_order = ['imported', 'requires_initial_review', 'private',
                  'pending', 'published', 'expiring-soon', 'expired']

    keys = ['review_state', 'Type']

    @property
    def key_1(self):
        return self.keys[0]

    @property
    def key_2(self):
        try:
            return self.keys[1]
        except IndexError:
            return None

    def __init__(self, results):
        self.results = results

    def getSortOrder(self, x):

        try:
            return self.sort_order.index(x.get(self.key_1, ''))
        except ValueError:
            return 99999

    def __call__(self):

        data = {}

        for r in self.results:

            k = getattr(r, self.key_1)

            if not data.has_key(k):
                data[k] = {self.key_1 : k, 'brains' : []}

            data[k]['brains'].append(r)

        if self.key_2:
            for k in data.keys():
                data[k]['brains'].sort(key=lambda x: getattr(x, self.key_2, ''))

        return sorted(data.values(), key=self.getSortOrder)

class ContentByType(ContentByReviewState):

    keys = ['Type', 'review_state']
    sort_order = ['Article', 'Publication']

    @memoize
    def product_types(self):
        return sorted(list(set([x.Type for x in self.results])))

    @property
    def sort_order(self):
        return self.product_types()

class ContentByAuthorTypeStatus(ContentByReviewState):
    pass