from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import Container
from plone.app.content.interfaces import INameFromTitle
from plone.autoform import directives as form
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.interface import implements
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider

class IWebinarRecording(model.Schema):

    __doc__ = "Webinar Recording"

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

    watch_now = schema.Bool(
        title=_(u"Watch Now?"),
        required=False,
        default=True,
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

@provider(IFormFieldProvider)
class IWebinarPresentation(model.Schema):

    __doc__ = "Webinar Presentation"

    file = NamedBlobFile(
        title=_(u"Presentation File"),
    )

@provider(IFormFieldProvider)
class IWebinarHandout(model.Schema):

    __doc__ = "Webinar Handout"

    file = NamedBlobFile(
        title=_(u"Handout File"),
    )


