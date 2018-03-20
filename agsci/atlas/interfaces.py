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

class IEventMarker(IAPIDataAdapter):
    """
    Used to indicate an event
    """

class ICventEventMarker(IAPIDataAdapter):
    """
    Used to indicate an event
    """

class IEventGroupMarker(Interface):
    """
    Used to indicate an event group
    """

class IWorkshopMarker(IAPIDataAdapter):
    """
    Used to indicate a workshop
    """

class IWebinarMarker(IAPIDataAdapter):
    """
    Used to indicate a webinar
    """

class IWebinarRecordingMarker(IAPIDataAdapter):
    """
    Used to indicate a webinar recording
    """

class IWebinarRecordingFileMarker(IAPIDataAdapter):
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

class IPublicationMarker(IAPIDataAdapter):
    """
    Used to indicate a publication
    """

class IRegistrationFields(Interface):
    """
    Denotes something as having registration fields
    """

class IRegistrationFieldset(Interface):
    """
    Denotes something as being used in a registration fieldset
    """

class IRegistrationFieldsetMarker(IAPIDataAdapter):
    """
    Data adapter marker for objects that provide registraton fields.
    """

class IOnlineCourseMarker(IAPIDataAdapter):
    """
    Data adapter marker for online course products.
    """

class IAppMarker(IAPIDataAdapter):
    """
    Data adapter marker for applications.
    """

class ISmartSheetMarker(IAPIDataAdapter):
    """
    Data adapter marker for smartsheet.
    """

class IOnlineCourseGroupMarker(IAPIDataAdapter):
    """
    Used to indicate an online course group
    """

class ICountyMarker(IAPIDataAdapter):
    """
    Used to indicate a county
    """

class IPersonMarker(IAPIDataAdapter):
    """
    Used to indicate a person
    """

class ILocationMarker(Interface):
    """
    Used to adapt locatable objects
    """

class IEventGroupDurationMarker(IAPIDataAdapter):
    """
    Used to adapt event groups with duration objects
    """

class ICurriculumMarker(IAPIDataAdapter):
    """
    Used to indicate a curriculum
    """