from zope.interface import Interface

class IArticleMarker(Interface):
    """
    Used to indicate an article.
    """

class IVideoMarker(Interface):
    """
    Used to indicate an video.
    """

class ISlideshowMarker(Interface):
    """
    Used to indicate an slideshow.
    """

class IArticleArchetypesContent(Interface):
    """
    Used to indicate a piece of Archetypes content used in an article.  This 
    interface allows us to trigger workflow on CRUD of article content types.
    """
