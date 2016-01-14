from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from plone.namedfile.field import NamedBlobFile
from plone.autoform import directives as form
from behaviors import IWebinar
from plone.app.dexterity.behaviors.metadata import IBasic

class IWebinarRecording(model.Schema):

    speakers = schema.List(
        title=_(u"Speakers"),
        description=_(u"One per line"),
        value_type=schema.TextLine(),
    )

    link = schema.TextLine(
        title=_(u"Webinar Link"),
        required=True,
    )

class IWebinarPresentation(model.Schema):

    file = NamedBlobFile(
        title=_(u"Presentation File"),
    )

class IWebinarHandout(model.Schema):

    file = NamedBlobFile(
        title=_(u"Handout File"),
    )

    
