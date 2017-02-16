from apiclient.discovery import build
from urllib2 import urlopen
from agsci.leadimage.interfaces import ILeadImageMarker
from plone.namedfile.file import NamedBlobImage
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from ..content.adapters import VideoDataAdapter

def onVideoSave(context, event):

    # Check for lead image
    if not ILeadImageMarker(context).has_leadimage:

        # If no lead image exists, get the data via the YouTube API
        image_data = getImageForYouTubeVideo(context)

        # Set the lead image if we retrieved it
        if image_data:
            filename = '%s-leadimage' % context.getId()
            field = NamedBlobImage(filename.encode('utf-8'))
            field.data = image_data
            context.leadimage = field
            context.reindexObject()

def getAPIKey():
    registry = getUtility(IRegistry)
    return registry.get('agsci.atlas.youtube_api_key')

def getImageForYouTubeVideo(context):

    # Get video id and provider from video
    video_provider = VideoDataAdapter(context).getVideoProvider()
    video_id = VideoDataAdapter(context).getVideoId()

    # If video provider is not YouTube, return None
    if video_provider != 'YouTube':
        return None

    # Return nothing if we don't have a video id
    if not video_id:
        return None

    try:
        data = getDataForYouTubeVideo(video_id)
    except:
        data = {}

    url = data.get('leadimage', None)

    if url:
        try:
            return urlopen(url).read()
        except:
            return None

    return None


def getDataForYouTubeVideo(video_id):

    # Read this value from registry.  Hardcoded for testing.
    google_api_key = getAPIKey()

    # If no key, return empty dict
    if not google_api_key:
        return {}

    # This access scope allows for read-only access to the authenticated
    # user's account, but not other types of account access.
    YOUTUBE_READONLY_SCOPE = 'https://www.googleapis.com/auth/youtube.readonly'
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=google_api_key, cache_discovery=False)

    video_response = youtube.videos().list(id=video_id, part='snippet').execute()

    for video in video_response['items']:

        data = {}

        data['title'] = video['snippet']['title']
        data['description'] = video['snippet']['description']
        data['leadimage'] = video['snippet']['thumbnails'].get('high', {}).get('url', '')
        data['channel'] = video['snippet']['channelTitle']
        data['url'] = "http://www.youtube.com/watch?v=%s" % video['id']

        return data

    return {}
