from agsci.atlas import AtlasMessageFactory as _
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from plone.supermodel import model
from zope.interface import provider
from zope import schema

from agsci.atlas.permissions import *

@provider(IFormFieldProvider)
class IIgnoreChecksBase(model.Schema):

    # Only allow superusers to write to this field
    form.write_permission(ignore_checks=ATLAS_SUPERUSER)

    ignore_checks = schema.List(
        title=_(u"Ignore Checks"),
        description=_(u"Ids (classes) of check to be ignored."),
        value_type=schema.Choice(vocabulary="agsci.atlas.content_checks"),
        required=False,
    )

@provider(IFormFieldProvider)
class IContainerIgnoreChecks(IIgnoreChecksBase):

    model.fieldset(
        'settings',
        label=_(u'Settings'),
        fields=['ignore_checks'],
    )
    
@provider(IFormFieldProvider)
class IProductIgnoreChecks(IIgnoreChecksBase):

    model.fieldset(
        'internal',
        label=_(u'Internal'),
        fields=['ignore_checks'],
    )