from zope.interface import Interface
from agsci.api.interfaces import IAPIDataAdapter

class IArticleMarker(IAPIDataAdapter):
    """
    Used to indicate an article.
    """

class IVideoMarker(IAPIDataAdapter):
    """
    Used to indicate a video.
    """

class ISlideshowMarker(IAPIDataAdapter):
    """
    Used to indicate a slideshow.
    """

class INewsItemMarker(IAPIDataAdapter):
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

class IPDFDownloadMarker(IAPIDataAdapter):
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

class IPublicationMarker(IAPIDataAdapter):
    """
    Used to indicate a publication
    """