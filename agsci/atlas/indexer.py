
from content.behaviors import IAtlasMetadata
from plone.indexer import indexer
from zope.component import provideAdapter

# Indexers for content using the Atlas metadata
@indexer(IAtlasMetadata)
def AtlasCategory(context):

    return getattr(context, 'atlas_category', [])

provideAdapter(AtlasCategory, name='Category')

@indexer(IAtlasMetadata)
def AtlasProgram(context):

    return getattr(context, 'atlas_program', [])

provideAdapter(AtlasProgram, name='Program')


@indexer(IAtlasMetadata)
def AtlasTopic(context):

    return getattr(context, 'atlas_topic', [])

provideAdapter(AtlasTopic, name='Topic')

@indexer(IAtlasMetadata)
def AtlasSubtopic(context):

    return getattr(context, 'atlas_subtopic', [])

provideAdapter(AtlasSubtopic, name='Subtopic')

# Indexers for metadata structure
# TBD!