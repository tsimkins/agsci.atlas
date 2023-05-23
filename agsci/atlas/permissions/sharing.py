from zope.interface import implementer, Interface
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore import permissions as core_permissions

try:
    from plone.app.workflow.interfaces import ISharingPageRole
except ImportError:
    # Fail nicely, this version of Plone doesn't know anything about @@sharing page roles.
    class ISharingPageRole(Interface):
        pass

@implementer(ISharingPageRole)
class AtlasRole(object):
    title = _(u"Atlas Role")
    required_permission = core_permissions.ManagePortal

class SiteAdministratorRole(AtlasRole):
    title = _(u"Site Administrator")

class CventEditorRole(AtlasRole):
    title = _(u"Cvent Editor")

class EventGroupEditorRole(AtlasRole):
    title = _(u"Event Group Editor")

class OnlineCourseEditorRole(AtlasRole):
    title = _(u"Online Course Editor")

class PublicationEditorRole(AtlasRole):
    title = _(u"Publication Editor")

class VideoEditorRole(AtlasRole):
    title = _(u"Video Editor")

class DirectoryEditorRole(AtlasRole):
    title = _(u"Directory Editor")

class CurriculumEditorRole(AtlasRole):
    title = _(u"Curriculum Editor")
