from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import Container
from agsci.atlas.interfaces import IWebinarRecordingMarker
from plone.app.content.interfaces import INameFromTitle
from plone.autoform import directives as form
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implements, implementer

class IWebinarRecording(model.Schema):

    form.mode(title='hidden')

    title = schema.TextLine(
        title=_(u"Webinar Title"),
        required=True,
        default=_(u'Webinar Recording'),
    )

    webinar_recorded_url = schema.TextLine(
        title=_(u"Recorded Webinar Link"),
        required=True,
    )

    duration_formatted = schema.TextLine(
        title=_(u"Duration"),
        description=_(u"Formatted as HH:MM:SS"),
        required=True,
    )

    transcript = schema.Text(
        title=_(u"Transcript"),
        description=_(u"Plain text transcript of webinar"),
    )


class WebinarRecording(Container):

    pass


# Adapter to automagically generate the title.
class ITitleFromWebinar(INameFromTitle):
    def title():
        """Return a processed title"""

class TitleFromWebinar(object):
    implements(ITitleFromWebinar)

    def __init__(self, context):
        self.context = context

    @property
    def title(self):
        return "Webinar Recording"


class IWebinarPresentation(model.Schema):

    file = NamedBlobFile(
        title=_(u"Presentation File"),
    )

class IWebinarHandout(model.Schema):

    file = NamedBlobFile(
        title=_(u"Handout File"),
    )


