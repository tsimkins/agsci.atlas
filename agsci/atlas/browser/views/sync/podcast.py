from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from plone.app.textfield.value import RichTextValue
from zope.event import notify

import transaction
import feedparser

from agsci.atlas import object_factory
from agsci.atlas.content.adapters import PodcastGroupDataAdapter, VideoDataAdapter
from agsci.atlas.content.sync import SyncContentImporter
from agsci.atlas.events.notifications import notifyOnProductWorkflow
from agsci.atlas.events.video import getYouTubePlaylistAPIData
from agsci.atlas.events.interfaces import AtlasImportEvent
from agsci.atlas.utilities import ploneify

from . import SyncContentView

class ImportPodcastView(SyncContentView):

    # Type to import
    product_type = 'Podcast'

    # Content Importer Object Class
    content_importer = SyncContentImporter

    @property
    def rss_item_dates(self):
        rv = {}

        rss_feed_url = getattr(self.context.aq_base, 'rss_feed_url', None)

        if rss_feed_url:
            feed = feedparser.parse(rss_feed_url)

            for _ in feed.entries:
                title = ploneify(_.get('title'))
                published = DateTime(_.published)
                rv[title] = published

        return rv

    @property
    def import_path(self):
        return self.context

    @property
    def adapted(self):
        return PodcastGroupDataAdapter(self.context)

    @property
    def videos(self):

        playlist_id = self.adapted.playlist_id

        if playlist_id:
            return getYouTubePlaylistAPIData(playlist_id)

        return []

    @property
    def podcast_video_ids(self):
        return [ VideoDataAdapter(x).getVideoId() for x in self.adapted.getPages() ]

    @property
    def podcast_import_data(self):
        podcast_video_ids = self.podcast_video_ids
        videos = self.videos

        new_videos = [x for x in videos if x.get('video_id', None) not in podcast_video_ids and 'private video' not in x.get('title').lower()]

        for _ in new_videos:
            video_description = _.get('description', None)
            description = text = None

            if video_description:
                dt = [x for x in video_description.split('\n') if x]
                description = dt.pop(0)
                text = "\n".join(['<p>%s</p>' % x for x in dt])

            yield {
                'product_type' : self.product_type,
                'name' : (" ".join(_.get('title').split())).strip(),
                'video_url' : _.get('url'),
                'short_description' : description,
                'owners' : getattr(self.context.aq_base, 'owners', []),
                'authors' : getattr(self.context.aq_base, 'authors', []),
                'description' : RichTextValue(
                            raw=text,
                            mimeType=u'text/html',
                            outputMimeType='text/x-html-safe').output
            }

    def requestValidation(self):
        return True

    def importContent(self):

        # Dates from RSS feed
        rss_item_dates = self.rss_item_dates

        # Create a list (rv) for return values of objects
        rv = []

        # Iterate through the list of objects to update, and import them
        for i in self.podcast_import_data:

            # Create new content importer object
            v = self.content_importer(i)

            # Import the object
            item = self.importObject(v)

            # If we have an item returned...
            if item:

                # Set effective date
                _title = ploneify(item.Title())
                _effective = rss_item_dates.get(_title, None)

                if _effective:
                    item.setEffectiveDate(_effective)

                # Set transcript
                adapted = VideoDataAdapter(item)
                transcript_data = adapted.getYouTubeTranscript()

                if transcript_data:
                    adapted.setTranscript(transcript_data)

                # Append the created/updated item to the rv list
                rv.append(item)

                # Notify that this item has been imported
                notify(AtlasImportEvent(item))
                
                # Submit for review
                self.portal_workflow.doActionFor(item, 'submit', comment='Podcast automatically created and submitted.')
                
                item.reindexObject()
                
                # Send emails
                event = object_factory(action='submit')
                notifyOnProductWorkflow(item, event)
                
                transaction.commit()

        # Commit the transaction after the update/create so the getJSON() call
        # returns the correct values. This feels like really bad idea, but
        # it appears to work.
        transaction.commit()

        # Return the JSONified version of the list of items
        return self.getJSON(rv)

    @property
    def portal_workflow(self):
        return getToolByName(self.context, 'portal_workflow')