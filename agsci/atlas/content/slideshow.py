from agsci.atlas import AtlasMessageFactory as _
from plone.supermodel import model
from zope import schema
from plone.app.textfield import RichText


class ISlideshow(model.Schema):

    text = RichText(
        title=_(u"Body Text"),
        required=True
    )