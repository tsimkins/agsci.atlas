from . import StaticVocabulary
from zope.component.hooks import getSite
from agsci.atlas.utilities import ploneify
from agsci.atlas.constants import DELIMITER

class BaseEPASVocabulary(StaticVocabulary):

    fields = []

    @property
    def data(self):
        site = getSite()

        # Traverse to the TSV file containing EPAS data
        resource = site.restrictedTraverse('++resource++agsci.atlas/epas.tsv')

        # Get the config contents
        data = open(resource.context.path, "r").read()
        data = data.strip().replace("\r", "\n")
        data = [x.strip().split("\t") for x in data.split("\n")]

        # Get the headings row
        headings = [ploneify(x) for x in data.pop(0)]

        return [
            dict(zip(headings, x)) for x in data
        ]

    def encode_value(self, i):
        v = [i.get(x, '') for x in self.fields]

        if v[-1]:
            return DELIMITER.join(v)

    @property
    def items(self):

        v = [self.encode_value(x) for x in self.data]

        v = [x for x in v if x]

        return sorted(set(v))

class UnitVocabulary(BaseEPASVocabulary):

    fields = ['unit', ]

class TeamVocabulary(BaseEPASVocabulary):

    fields = ['unit', 'team']

class TopicVocabulary(BaseEPASVocabulary):

    fields = ['unit', 'team', 'topic']

UnitVocabularyFactory = UnitVocabulary()
TeamVocabularyFactory = TeamVocabulary()
TopicVocabularyFactory = TopicVocabulary()