from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import provider

from .. import IAtlasProduct
from ..video import IVideo

@provider(IFormFieldProvider)
class IPodcast(IVideo):

    __doc__ = "Podcast"

class Podcast(Item):
    pass
