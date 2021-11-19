from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.globalrequest import getRequest
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.component import getAdapters
from zope.interface import implements
from agsci.atlas.content.event.group import IEventGroup
from agsci.atlas.content.online_course.group import IOnlineCourseGroup
from agsci.atlas.content.adapters import EventDataAdapter
from agsci.atlas.interfaces import IEventGroupPolicy
from agsci.atlas.utilities import increaseHeadingLevel


# Views for rendering policies
class BasePolicyView(object):

    label = "Base Policy"
    sort_order = 1
    template = None

    def __init__(self, context):
        self.context = context

    @property
    def request(self):
        return getRequest()

    def __call__(self):

        if self.template:
            index = ViewPageTemplateFile(self.template)
            return increaseHeadingLevel(index(self))

        return "[Policy for %s]" % self.label

class COVIDPolicyView(BasePolicyView):

    label = "COVID-19 Policy"
    template = "templates/covid_policy.pt"


class SamplePolicyView(BasePolicyView):

    label = "Sample Policy"
    template = "templates/sample_policy.pt"

# Policy vocabulary
class EventGroupPolicyVocabulary(object):

    implements(IVocabularyFactory)

    # Returns a list of fieldsets sorted in order
    def getPolicies(self, context):

        _ = [x for x in getAdapters((context, ), IEventGroupPolicy)]

        _.sort(key=lambda x: (x[1].sort_order, x[1].label))

        return _

    def __call__(self, context):

        # Check the request to make sure this is not being triggered by an import
        try:
            request_url = context.REQUEST.getURL()
        except:
            # Can't get the URL, don't do anything
            pass
        else:
            # If the URL contains '++add++', context is actually the container.
            # Do a check to see if IEventGroup is provided by the parent.
            if '++add++' in request_url:
                if IEventGroup.providedBy(context) or \
                   IOnlineCourseGroup.providedBy(context):
                    return SimpleVocabulary([])

        # If this context has a parent that's an IEventGroup, return an empty
        # vocabulary
        if EventDataAdapter(context).getParentId():
            return SimpleVocabulary([])

        # Initialize items list
        items = []

        # Iterate through fieldsets, and append to items
        for (name, _) in self.getPolicies(context):
            items.append(SimpleTerm(name, title=_.label))

        # Return a SimpleVocabulary of these items
        return SimpleVocabulary(items)

EventGroupPolicyVocabularyFactory = EventGroupPolicyVocabulary()