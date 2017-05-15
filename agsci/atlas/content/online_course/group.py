from plone.dexterity.content import Container
from plone.supermodel import model

from agsci.atlas import AtlasMessageFactory as _
from agsci.atlas.content import IAtlasProduct
from ..behaviors import IOptionalVideo
from ..event.group import IRegistrationFields

class IOnlineCourseGroup(IOptionalVideo, IAtlasProduct, IRegistrationFields):

    model.fieldset(
        'registration',
        label=_(u'Registration'),
        fields=['registration_fieldsets',],
    )

class OnlineCourseGroup(Container):

    pass
