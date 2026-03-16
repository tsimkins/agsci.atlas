from plone.dexterity.content import Container
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import IAtlasProduct


class IPodcastGroup(IAtlasProduct):

    __doc__ = "Podcast Group"

    playlist_url = schema.TextLine(
        title=_(u"YouTube Playlist URL"),
        required=True,
    )

    rss_feed_url = schema.TextLine(
        title=_(u"RSS Feed URL"),
        required=True,
    )
    
    apple_podcasts_url = schema.TextLine(
        title=_(u"Apple Podcasts URL"),
        required=False,
    )

    amazon_music_url = schema.TextLine(
        title=_(u"Amazon Music URL"),
        required=False,
    )
    
    spotify_url = schema.TextLine(
        title=_(u"Spotify URL"),
        required=False,
    )

    podcast_addict_url = schema.TextLine(
        title=_(u"Podcast Addict URL"),
        required=False,
    )

class PodcastGroup(Container):
    pass
