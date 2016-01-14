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
