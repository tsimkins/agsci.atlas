from plone.dexterity.content import Container
from plone.supermodel import model

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import IAtlasProduct
from ..event import IRegistrationFields

class IOnlineCourseGroup(IAtlasProduct, IRegistrationFields):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',],
    )

class OnlineCourseGroup(Container):

    pass
