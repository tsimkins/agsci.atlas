from plone.autoform import directives as form
from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.interfaces import IEventGroupMarker
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from plone.dexterity.content import Container
from plone.app.textfield import RichText
from zope.schema.vocabulary import SimpleTerm
from agsci.atlas.content import IAtlasProduct

class IEventGroup(IAtlasProduct):

    pass
        

class EventGroup(Container):

    pass
