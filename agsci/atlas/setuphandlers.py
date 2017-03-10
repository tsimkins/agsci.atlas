# From http://maurits.vanrees.org/weblog/archive/2009/12/catalog

import logging
from plone.registry.interfaces import IRegistry
from plone.registry.record import Record
from plone.registry import field
from zope.component import getUtility
from Products.CMFCore.utils import getToolByName
from .indexer import filter_sets

# The profile id of your package:
PROFILE_ID = 'profile-agsci.atlas:default'

def add_catalog_indexes(context, logger=None):
    """Method to add our wanted indexes to the portal_catalog.

    @parameters:

    When called from the import_various method below, 'context' is
    the plone site and 'logger' is the portal_setup logger.  But
    this method can also be used as upgrade step, in which case
    'context' will be portal_setup and 'logger' will be None.
    """
    if logger is None:
        # Called as upgrade step: define our own logger.
        logger = logging.getLogger('agsci.atlas')

    # Run the catalog.xml step as that may have defined new metadata
    # columns.  We could instead add <depends name="catalog"/> to
    # the registration of our import step in zcml, but doing it in
    # code makes this method usable as upgrade step as well.  Note that
    # this silently does nothing when there is no catalog.xml, so it
    # is quite safe.
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'catalog')

    catalog = getToolByName(context, 'portal_catalog')
    indexes = catalog.indexes()
    # Specify the indexes you want, with ('index_name', 'index_type')
    wanted = [
                ('OriginalPloneIds', 'KeywordIndex'),
                ('CategoryLevel1', 'KeywordIndex'),
                ('CategoryLevel2', 'KeywordIndex'),
                ('CategoryLevel3', 'KeywordIndex'),

                ('StateExtensionTeam', 'KeywordIndex'),
                ('ProgramTeam', 'KeywordIndex'),
                ('Curriculum', 'KeywordIndex'),

                ('Authors', 'KeywordIndex'),
                ('Owners', 'KeywordIndex'),

                ('County', 'KeywordIndex'),

                ('CventId', 'FieldIndex'),
                ('EdxId', 'FieldIndex'),
                ('SKU', 'FieldIndex'),
                ('SalesforceId', 'FieldIndex'),

                ('ContentIssues', 'FieldIndex'),
                ('ContentErrorCodes', 'KeywordIndex'),
                ('cksum', 'FieldIndex'),

                ('IsChildProduct', 'FieldIndex'),
             ]

    # Add filterset keyword indexes
    for filter_set in filter_sets():
        wanted.append((filter_set, 'KeywordIndex'))

    indexables = []
    for name, meta_type in wanted:
        if name not in indexes:
            catalog.addIndex(name, meta_type)
            indexables.append(name)
            logger.info("Added %s for field %s.", meta_type, name)
    if len(indexables) > 0:
        logger.info("Indexing new indexes %s.", ', '.join(indexables))
        catalog.manage_reindexIndex(ids=indexables)

# Create keys with a default initial value that can be changed, and not
# overridden by reinstalls.
def create_registry_keys(site, logger):
    registry = getUtility(IRegistry)

    keys = [
        (
            'agsci.atlas.youtube_api_key',
            Record(field.TextLine(title=u'YouTube API Key'),
                   u'')
        ),
        (
            'agsci.atlas.google_maps_api_key',
            Record(field.TextLine(title=u'Google Maps API Key'),
                   u'')
        ),
        (
            'agsci.atlas.api_debug',
            Record(field.Bool(title=u'Atlas API Debugging'),
                  False)
        ),
    ]

    for (key, value) in keys:

        if not registry.get(key):
            registry.records[key] = value
            logger.info("Added key %s" % key)
        else:
            logger.info("Key %s exists. Did not add." % key)


def import_various(context):
    """Import step for configuration that is not handled in xml files.
    """
    # Only run step if a flag file is present
    if context.readDataFile('agsci.atlas.marker.txt') is None:
        return
    logger = context.getLogger('agsci.atlas')
    site = context.getSite()
    add_catalog_indexes(site, logger)
    create_registry_keys(site, logger)
