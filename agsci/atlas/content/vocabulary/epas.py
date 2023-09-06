import csv

from . import StaticVocabulary
from zope.component.hooks import getSite
from zope.security import checkPermission
from zope.security.interfaces import NoInteraction
from agsci.atlas.utilities import ploneify
from agsci.atlas.constants import DELIMITER
from agsci.atlas.permissions import ATLAS_SUPERUSER

class BaseEPASVocabulary(StaticVocabulary):

    fields = []

    admin_values = [
        [
            'Non-College',
            'College of Engineering',
            'College of Engineering',
        ],
        [
            'Non-College',
            'College of Nursing',
            'College of Nursing',
        ],
        [
            'College of Agricultural Sciences',
            'Ag Sciences Global',
            'Ag Sciences Global',
        ],
    ]

    @property
    def site(self):
        return getSite()

    @property
    def is_admin(self):
        try:
            return checkPermission(ATLAS_SUPERUSER, self.site)
        except NoInteraction:
            return True

    @property
    def data(self):

        # Traverse to the TSV file containing EPAS data
        resource = self.site.restrictedTraverse('++resource++agsci.atlas/epas.tsv')

        # Get the config contents
        data = []

        with open(resource.context.path, 'r') as csvfile:

            csv_reader = csv.reader(csvfile, delimiter='\t', quotechar='"')

            for row in csv_reader:
                data.append(row)

        # Add admin-only values if we're an admin
        if self.is_admin:
            data.extend(self.admin_values)

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
