from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.component import getUtility
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory, IVocabularyFactory

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import IAtlasProduct

@provider(IContextAwareDefaultFactory)
def defaultRegistrationFieldsets(context):

    vocab = getUtility(IVocabularyFactory, "agsci.atlas.RegistrationFieldsets")

    values = vocab(context)

    if values:
        return vocab.getDefaults(context)

class IRegistrationFields(model.Schema):

    registration_fieldsets = schema.List(
        title=_(u"Registration Fieldsets"),
        description=_(u"Determines fields used in Magento registration form. "
                      u"Defaults are 'Basic' and 'Accessibility', and these will "
                      u"be used even if deselected."),
        value_type=schema.Choice(vocabulary="agsci.atlas.RegistrationFieldsets"),
        required=False,
        defaultFactory=defaultRegistrationFieldsets
    )

class IEventGroup(IRegistrationFields, IAtlasProduct):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',]
    )

class EventGroup(Container):

    pass
