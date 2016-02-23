from zope.interface import Interface
from plone.app.event.dx.interfaces import IDXEvent as _IDXEvent

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

class INewsContainerMarker(Interface):
    """
    Used to indicate a news container.
    """

class IEventsContainerMarker(Interface):
    """
    Used to indicate an events container.
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