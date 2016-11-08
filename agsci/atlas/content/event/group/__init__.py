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
from agsci.atlas.content.event import IRegistrationFields

class IEventGroup(IRegistrationFields, IAtlasProduct):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',]
    )

class EventGroup(Container):

    pass
