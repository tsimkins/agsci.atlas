from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.interface import provider
from plone.autoform import directives as form
from zope import schema
from zope.schema.interfaces import IContextAwareDefaultFactory
from plone.app.dexterity.behaviors.metadata import MetadataBase, DCFieldProperty
from z3c.form.interfaces import IEditForm, IAddForm

from agsci.atlas.content import getMetadataByContentType

def defaultMetadataFactory(context, content_type):
    v = getMetadataByContentType(context, content_type)
    
    if v:
        return [v]
        
    return v

@provider(IContextAwareDefaultFactory)
def defaultCategory(context):
    return defaultMetadataFactory(context, 'Category')

@provider(IContextAwareDefaultFactory)
def defaultProgram(context):
    return defaultMetadataFactory(context, 'Program')

@provider(IContextAwareDefaultFactory)
def defaultTopic(context):
    return defaultMetadataFactory(context, 'Topic')

@provider(IContextAwareDefaultFactory)
def defaultSubtopic(context):
    return defaultMetadataFactory(context, 'Subtopic')


@provider(IFormFieldProvider)
class IAtlasMetadata(model.Schema):

    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('atlas_category', 'atlas_program', 'atlas_topic', 'atlas_subtopic',),
        )

    atlas_category = schema.List(
            title=_(u"Category"),
            description=_(u""),
            required=False,
            value_type=schema.Choice(vocabulary="agsci.atlas.Category"),
            defaultFactory=defaultCategory,
        )

    atlas_program = schema.List(
            title=_(u"Program"),
            description=_(u""),
            required=False,
            value_type=schema.Choice(vocabulary="agsci.atlas.Program"),
            defaultFactory=defaultProgram,
        )

    atlas_topic = schema.List(
            title=_(u"Topic"),
            description=_(u""),
            required=False,
            value_type=schema.Choice(vocabulary="agsci.atlas.Topic"),
            defaultFactory=defaultTopic,
        )

    atlas_subtopic = schema.List(
            title=_(u"Subtopic"),
            description=_(u""),
            required=False,
            value_type=schema.Choice(vocabulary="agsci.atlas.Subtopic"),
            defaultFactory=defaultSubtopic,
        )

@provider(IFormFieldProvider)
class IWebinar(model.Schema):

    model.fieldset(
        'dates',
        label=_(u'Dates'),
        fields=['expires'],
    )

    effective = schema.Datetime(
        title=_(u'Webinar Date'),
        description=_(u'Date on which webinar was originally held.'),
        required=True
    )

    expires = schema.Datetime(
        title=_(u'Expiration Date'),
        description=_(u"When this date is reached, the content will no"
                      u"longer be visible in listings and searches."),
        required=False
    )

    form.omitted('effective', 'expires')
    form.no_omit(IEditForm, 'effective', 'expires')
    form.no_omit(IAddForm, 'effective', 'expires')


class Webinar(MetadataBase):
    effective = DCFieldProperty(
        IWebinar['effective'],
        get_name='effective_date'
    )
    expires = DCFieldProperty(
        IWebinar['expires'],
        get_name='expiration_date'
    )
