from plone.app.textfield import RichText
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from zope import schema
from zope.interface import provider

from agsci.atlas import AtlasMessageFactory as _
from . import IArticleDexterityContainedContent, IAtlasProduct
from .behaviors import IVideoBase

class IArticleVideo(IVideoBase, IArticleDexterityContainedContent):

    pass

@provider(IFormFieldProvider)
class IVideo(IVideoBase, IAtlasProduct):

    __doc__ = "Video (Product)"

    transcript = RichText(
        title=_(u"Transcript"),
        required=False,
    )

    video_duration_milliseconds = schema.Int(
        title=_(u"Video Length (In Milliseconds)"),
        required=False,
    )


class BaseVideo(Item):

    pass

class ArticleVideo(BaseVideo):

    pass

class Video(ArticleVideo):

    pass