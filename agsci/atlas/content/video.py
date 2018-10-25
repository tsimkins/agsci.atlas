from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import provider

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.permissions import *
from . import IArticleDexterityContainedContent, IAtlasProduct
from .behaviors import IVideoBase

class IArticleVideo(IVideoBase, IArticleDexterityContainedContent):

    pass

@provider(IFormFieldProvider)
class IVideo(IVideoBase, IAtlasProduct):

    __doc__ = "Video (Product)"

    form.write_permission(video_duration_milliseconds=ATLAS_SUPERUSER)

    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['transcript', 'video_duration_milliseconds'],
    )

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