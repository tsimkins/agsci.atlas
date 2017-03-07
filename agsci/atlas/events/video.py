from apiclient.discovery import build
from urllib2 import urlopen
from agsci.leadimage.interfaces import ILeadImageMarker
from plone.namedfile.file import NamedBlobImage
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component.hooks import getSite

import isodate

from ..content.adapters import VideoDataAdapter

# Action taken when a video is saved
def onVideoSave(context, event, force=True):

    # Updated flag
    updated = False

    # Check if we have missing fields
    has_leadimage = not not ILeadImageMarker(context).has_leadimage
    has_duration = not not VideoDataAdapter(context).getDuration()
    has_channel = not not VideoDataAdapter(context).getVideoChannel()
    has_aspect_ratio = not not VideoDataAdapter(context).getVideoAspectRatio()

    # If 'force' is true, or doesn't have a lead image and duration.
    if force or not has_leadimage or not has_duration \
             or not has_channel or not has_aspect_ratio:

        # Get the API data
        data = getDataForYouTubeVideo(context)

        # Lead Image (if force or not exists)
        if force or not has_leadimage:

            # Get the image data via the YouTube API
            # (will be binary data)
            image_data = getImageForYouTubeVideo(data)

            # Set the lead image if we retrieved it
            if image_data:
                filename = '%s-leadimage' % context.getId()
                field = NamedBlobImage(filename.encode('utf-8'))
                field.data = image_data
                context.leadimage = field
                updated = True

        # Duration (if force or not exists)
        if force or not has_duration:

            # Get the duration from the API data
            # (will be integer)
            duration = data.get('duration', None)

            # If there's a duration, set it.
            if duration:
                VideoDataAdapter(context).setDuration(duration)
                updated = True

        # Channel (if force or not exists)
        if force or not has_channel:

            # Get the channel id from the API data
            # (will be string)
            channel_id = data.get('channel_id', None)

            # If there's a channel id, set it.
            if channel_id:
                VideoDataAdapter(context).setVideoChannel(channel_id)
                updated = True

        # Aspect Ratio (if force or not exists)
        if force or not has_aspect_ratio:

            # Get the aspect_ratio from the API data
            # (will be string)
            aspect_ratio = data.get('aspect_ratio', None)

            # If there's a Aspect Ratio, set it.
            if aspect_ratio:
                VideoDataAdapter(context).setVideoAspectRatio(aspect_ratio)
                updated = True

        # If we updated a value, reindex the object
        if updated:
            context.reindexObject()

# Returns the value of the API key from the registry
def getAPIKey():
    registry = getUtility(IRegistry)
    return registry.get('agsci.atlas.youtube_api_key')

# Given the return data from the API, extracts the leadimage URL (remote) and
# downloads the image.
def getImageForYouTubeVideo(data):

    url = data.get('leadimage', None)

    if url:
        try:
            return urlopen(url).read()
        except:
            return None

    return None

def getDataForYouTubeVideo(context):

    # Get video id and provider from video
    video_provider = VideoDataAdapter(context).getVideoProvider()
    video_id = VideoDataAdapter(context).getVideoId()

    # If video provider is not YouTube, return None
    if video_provider != 'YouTube':
        return {}

    # Return nothing if we don't have a video id
    if not video_id:
        return {}

    try:
        data = getYouTubeAPIData(video_id)
    except:
        data = {}

    return data

# Returns the duration in milliseconds given a ISO-8601 duration (e.g. u'PT6M55S')
def formatDuration(v):

    if v:
        try:
            duration = isodate.parse_duration(v)
            return int(duration.total_seconds()*1000)
        except:
            return None

    return None

# Return either 16:9, 3:2, or 4:3

def formatAspectRatio(x,y):

    # Guess a default
    default = u'16:9'

    # If both x and y are digits, calculate the closest standard ratio in the
    # vocabulary
    if x.isdigit() and y.isdigit():

        # Calculate actual ratio
        x = float(x)
        y = float(y)

        video_ratio = x/y # The calculated aspect ratio of the video

        # Temporary array for holding vocab term and abs difference of actual ratio
        data = []

        # Get the VideoAspectRatio vocabulary values
        aspect_ratios = VideoDataAdapter(getSite()).video_aspect_ratios

        # Cycle through aspect_ratios, calculating abs difference between vocab ratio and actual ratio
        for i in aspect_ratios:

            (v_x, v_y) = [float(x) for x in i.split(':')[0:2]]

            vocab_ratio = v_x/v_y

            diff_percentage = abs((vocab_ratio-video_ratio)/vocab_ratio)

            data.append([diff_percentage, i])

        # Sort data by diff_percentage
        data.sort(key=lambda x: x[0])

        # Return the value of the closest aspect ratio
        return data[0][1]

    return default

def getYouTubeAPIData(video_id):

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

    video_response = youtube.videos().list(id=video_id,
                                           part='snippet,contentDetails,player',
                                           maxWidth=1200.0).execute()

    for video in video_response['items']:

        data = {}

        data['title'] = video['snippet']['title']
        data['description'] = video['snippet']['description']
        data['leadimage'] = video['snippet']['thumbnails'].get('high', {}).get('url', '')
        data['channel'] = video['snippet']['channelTitle']
        data['channel_id'] = video['snippet']['channelId']
        data['url'] = "http://www.youtube.com/watch?v=%s" % video['id']
        data['duration'] = formatDuration(video['contentDetails'].get('duration', None))

        # Calculate aspect ratio
        data['width'] = video.get('player', {}).get('embedWidth', 0)
        data['height'] = video.get('player', {}).get('embedHeight', 0)
        data['aspect_ratio'] = formatAspectRatio(data['width'], data['height'])

        return data

    return {}
