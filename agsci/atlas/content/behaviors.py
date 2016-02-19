from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.interface import provider
from plone.autoform import directives as form
from zope import schema
from zope.schema.interfaces import IContextAwareDefaultFactory
from plone.app.dexterity.behaviors.metadata import MetadataBase, DCFieldProperty
from z3c.form.interfaces import IEditForm, IAddForm

from agsci.atlas.content import getDefaultMetadataIdByContentType

def defaultMetadataFactory(context, content_type):
    v = getDefaultMetadataIdByContentType(context, content_type)

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


@provider(IFormFieldProvider)
class IAtlasMetadata(model.Schema):

    # Categorization

    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('atlas_category', 'atlas_program', 'atlas_topic', 
                    'atlas_filters', 'atlas_home_or_commercial', 
                    'atlas_language'),
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

    atlas_filters = schema.List(
            title=_(u"Filters"),
            description=_(u""),
            required=False,
            value_type=schema.Choice(vocabulary="agsci.atlas.Filters"),
        )

    atlas_language = schema.Choice(
        title=_(u"Language"),
        vocabulary="agsci.atlas.Language",
        required=True,
    )

    atlas_home_or_commercial = schema.List(
        title=_(u"Home or Commercial"),
        value_type=schema.Choice(vocabulary="agsci.atlas.HomeOrCommercial"),
        required=False,
    )

    additional_information = schema.Text(
        title=_(u"Additional Information"),
        required=False,
    )

    # Internal
    model.fieldset(
            'internal',
            label=_(u'Internal'),
            fields=('sku', 'internal_comments', ),
        )

    sku = schema.TextLine(
            title=_(u"SKU"),
            description=_(u""),
            required=False,
        )

    internal_comments = schema.Text(
        title=_(u"Internal Comments"),
        required=False,
    )

@provider(IFormFieldProvider)
class IAtlasAudience(model.Schema):

    # Categorization

    model.fieldset(
            'categorization',
            label=_(u'Categorization'),
            fields=('atlas_audience', 'atlas_knowledge'),
        )

    atlas_audience = schema.Text(
        title=_(u"Who is this for?"),
        required=False,
    )

    atlas_knowledge = schema.Text(
        title=_(u"What will you learn?"),
        required=False,
    )

class IAtlasPaid(model.Schema):

    length_content_access = schema.Int(
        title=_(u"Length of Access"),
        required=False,
    )


@provider(IFormFieldProvider)
class IAtlasOwnership(model.Schema):

    model.fieldset(
            'ownership',
            label=_(u'Ownership'),
            fields=('owners', 'contacts', 'authors'),
        )

    owners = schema.List(
            title=_(u"Owner"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            required=True
        )

    contacts = schema.List(
            title=_(u"Contacts"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            required=False
        ) 
        
    authors = schema.List(
            title=_(u"Authors / Instructors / Speakers"),
            description=_(u""),
            value_type=schema.TextLine(required=True),
            required=False
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
