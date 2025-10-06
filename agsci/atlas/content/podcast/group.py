from plone.dexterity.content import Container
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import IAtlasProduct


class IPodcastGroup(IAtlasProduct):

    __doc__ = "Podcast Group"

    playlist_url = schema.TextLine(
        title=_(u"Playlist URL"),
        required=True,
    )

    rss_feed_url = schema.TextLine(
        title=_(u"RSS Feed URL"),
        required=True,
    )

class PodcastGroup(Container):
    pass
