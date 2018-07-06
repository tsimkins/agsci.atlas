# Catalog logic from http://maurits.vanrees.org/weblog/archive/2009/12/catalog

import logging
from plone.registry.interfaces import IRegistry
from plone.registry.record import Record
from plone.registry import field
from zope.component import getUtility, getUtilitiesFor
from Products.CMFCore.utils import getToolByName
from .indexer import filter_sets
from .utilities import ploneify
from .content.vocabulary import IRegistryVocabularyFactory

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

                ('EducationalDrivers', 'KeywordIndex'),

                ('StateExtensionTeam', 'KeywordIndex'),
                ('ProgramTeam', 'KeywordIndex'),
                ('Curriculum', 'KeywordIndex'),

                ('Authors', 'KeywordIndex'),
                ('Owners', 'KeywordIndex'),

                ('County', 'KeywordIndex'),

                ('CventId', 'FieldIndex'),
                ('EdxId', 'FieldIndex'),
                ('SKU', 'FieldIndex'),
                ('MagentoURL', 'FieldIndex'),
                ('SalesforceId', 'FieldIndex'),

                ('ContentIssues', 'FieldIndex'),
                ('ContentErrorCodes', 'KeywordIndex'),
                ('cksum', 'FieldIndex'),

                ('IsChildProduct', 'FieldIndex'),
                ('IsFeaturedProduct', 'FieldIndex'),
                ('IsHiddenProduct', 'FieldIndex'),

                ('atlas_language', 'KeywordIndex'),

                ('homepage_topics', 'KeywordIndex'),

                ('content_owner_modified', 'DateIndex'),
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

    vocab_reset_key = 'agsci.atlas.default_vocabulary_reset'

    keys = [
        (
            'agsci.atlas.environment',
            Record(field.TextLine(title=u'Environment Name', required=False)),
            u''
        ),
        (
            'agsci.atlas.youtube_api_key',
            Record(field.TextLine(title=u'YouTube API Key')),
            u''
        ),
        (
            'agsci.atlas.google_maps_api_key',
            Record(field.TextLine(title=u'Google Maps API Key')),
            u''
        ),
        (
            'agsci.atlas.jitterbit.product_update_endpoint_url',
            Record(field.TextLine(title=u'Jitterbit Product Update Endpoint URL')),
            u''
        ),
        (
            'agsci.atlas.api_debug',
            Record(field.Bool(title=u'Atlas API Debugging')),
            False
        ),
        (
            'agsci.atlas.magento_integration_enable',
            Record(field.Bool(title=u'Enable Magento Integration')),
            False
        ),
        (
            'agsci.atlas.api_cache',
            Record(field.Bool(title=u'Atlas API Results Caching Enabled')),
            True
        ),
        (
            'agsci.atlas.notification_enable',
            Record(field.Bool(title=u'Workflow Notification: Enable?')),
            False
        ),
        (
            'agsci.atlas.notification_debug',
            Record(field.Bool(title=u'Workflow Notification: Debug Mode?')),
            True
        ),
        (
            'agsci.atlas.notification_debug_email',
            Record(field.TextLine(title=u'Workflow Notification: Debug Mode email')),
            u'tsimkins@psu.edu'
        ),
        (
            'agsci.atlas.notification_web_team_email',
            Record(field.TextLine(title=u'Workflow Notification: Web Team Email')),
            u'webservices@ag.psu.edu'
        ),
        (
            vocab_reset_key,
            Record(field.Tuple(title=u'Vocabularies to reset to default', value_type=field.TextLine())),
            ()
        ),
    ]

    overrides = registry.get(vocab_reset_key, [])

    # IRegistryVocabularyFactory Vocabularies
    for (name, vocab) in getUtilitiesFor(IRegistryVocabularyFactory):
        keys.append(
            (
                name,
                Record(field.Tuple(title=vocab.__doc__, value_type=field.TextLine())),
                tuple(vocab.defaults)
            )
        )

    for (key, record, value) in keys:

        if key not in registry or key in overrides:
            record.value = value
            registry.records[key] = record
            logger.info("Added key %s" % key)
        else:
            logger.info("Key %s exists. Did not add." % key)

# Creates editor groups for various product types
def create_groups(site, logger):

    # Group, role, people

    config = [
        [
            u'News Reviewers',
            u'News Reviewer',
            [
                'tab36',
            ]
        ],
        [
            u'Cvent Editors',
            u'Cvent Editor',
            [
                'dkk2',
                'mer5012',
            ]
        ],
        [
            u'Directory Editors',
            u'Directory Editor',
            [
                'dqm6',
                'dss9',
                'mbf5',
                'tlf2',
                'tut94',
            ]
        ],
        [
            u'Event Group Editors',
            u'Event Group Editor',
            [
                'dkk2',
                'mer5012',
            ]
        ],
        [
            u'Online Course Editors',
            u'Online Course Editor',
            [
                'eag154',
                'rar160',
            ],
        ],
        [
            u'Publication Editors',
            u'Publication Editor',
            [
                'aer127',
            ]
        ],
        [
            u'Video Editors',
            u'Video Editor',
            [
                'eag154',
                'aah41',
            ]
        ],
        [
            u'Curriculum Editors',
            u'Curriculum Editor',
            [
                'eag154',
                'rar160',
            ]
        ],
        [
            u'Analytics Viewers',
            u'Analytics Viewer',
            [
                'trs22',
                'kew176',
                'wmh5034',
            ]
        ],
    ]

    # Get the group tool
    grouptool = getToolByName(site, 'portal_groups')

    # Add groups, set title, set roles, add people
    for (group_name, site_role, people) in config:

        logger.info("Adding %s" % group_name)

        group_id = ploneify(group_name)

        grouptool.addGroup(group_id)

        group = grouptool.getGroupById(group_id)

        group.setGroupProperties({'title' : group_name})

        grouptool.editGroup(group_id, roles=[site_role,])

        for _id in people:

            logger.info("Adding %s to %s" % (_id, group_name))

            group.addMember(_id)


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
    create_groups(site, logger)