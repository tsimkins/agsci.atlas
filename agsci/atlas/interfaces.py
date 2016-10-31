from zope.interface import Interface

class IArticleMarker(Interface):
    """
    Used to indicate an article.
    """

class IVideoMarker(Interface):
    """
    Used to indicate a video.
    """

class ISlideshowMarker(Interface):
    """
    Used to indicate a slideshow.
    """

class INewsItemMarker(Interface):
    """
    Used to indicate a news item.
    """

class IEventMarker(Interface):
    """
    Used to indicate an event
    """

class IEventGroupMarker(Interface):
    """
    Used to indicate an event group
    """

class IWebinarRecordingMarker(Interface):
    """
    Used to indicate a webinar recording
    """

class IAtlasStructureMarker(Interface):
    """
    Used to indicate an Atlas container
    """

class IExtensionStructureMarker(Interface):
    """
    Used to indicate an Extension Structure container
    """

class IPDFDownloadMarker(Interface):
    """
    Used to indicate an item with a downloadable PDF
    """

class IAtlasProductReport(Interface):
    """
    Used to indicate objects that are able to have product reports run against them.
    """

class IAtlasVideoFields(Interface):
    """
    Used to indicate objects that have the video fields
    """

class IPublicationMarker(Interface):
    """
    Used to indicate a publication
    """