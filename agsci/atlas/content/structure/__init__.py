from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import implements
from eea.facetednavigation.interfaces import IFacetedNavigable, \
                                             IDisableSmartFacets, \
                                             IHidePloneRightColumn

from agsci.atlas import AtlasMessageFactory as _

from ..vocabulary.calculator import AtlasMetadataCalculator

class IAtlasStructure(model.Schema):
    pass

class ICategoryLevel1(IAtlasStructure):

    model.fieldset(
        'settings',
        label=_(u'Settings'),
        fields=['hide_from_top_nav', 'internal_store_category',],
    )

    hide_from_top_nav = schema.Bool(
        title=_(u"Hide from top navigation?"),
        description=_(u""),
        required=False,
        default=False,
    )

    internal_store_category = schema.Bool(
        title=_(u"Internal Store Category?"),
        description=_(u""),
        required=False,
        default=False,
    )

class ICategoryLevel2(IAtlasStructure):

    model.fieldset(
        'settings',
        label=_(u'Settings'),
        fields=['atlas_category_educational_drivers',],
    )

    atlas_category_educational_drivers = schema.List(
        title=_(u"Additional Educational Drivers"),
        value_type=schema.TextLine(required=True),
        required=False,
    )

class ICategoryLevel3(IAtlasStructure):

    atlas_filter_sets = schema.List(
        title=_(u"Filter Sets"),
        value_type=schema.Choice(vocabulary="agsci.atlas.FilterSet"),
        required=False,
    )

class AtlasStructure(Container):

    implements(IFacetedNavigable, IDisableSmartFacets, IHidePloneRightColumn)

    def getQueryForType(self):

        content_type = self.Type()

        mc = AtlasMetadataCalculator(content_type)

        metadata_value = mc.getMetadataForObject(self)

        return {content_type : metadata_value}

    @property
    def child_type(self):

        v = 'atlas_category_level_'

        _type = self.portal_type

        if _type.startswith(v):
            i = int(_type[-1]) + 1
            return '%s%d' % (v,i)

        return ''

    def _allowedContentTypes(self):

        # Get existing allowed types
        allowed_content_types = super(self.__class__, self).allowedContentTypes()

        # Remove some content types if we have a Category Level 3 inside us
        if self.listFolderContents({'portal_type' : self.child_type,}):

            # This is the list we'll be returning
            return [x for x in allowed_content_types if x.getId() == self.child_type]

        elif self.listFolderContents():
            return [x for x in allowed_content_types if x.getId() != self.child_type]

        return allowed_content_types


class CategoryLevel1(AtlasStructure):

    def allowedContentTypes(self):
        return self._allowedContentTypes()


class CategoryLevel2(AtlasStructure):

    def allowedContentTypes(self):
        return self._allowedContentTypes()


class CategoryLevel3(AtlasStructure):

    pass
