from agsci.atlas import AtlasMessageFactory as _
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from zope import schema
from zope.interface import provider
from . import Container, IAtlasProduct, IArticleDexterityContainedContent
from .behaviors import IOptionalVideo

# Curriculum Group: Contains simple or digital curriculums
@provider(IFormFieldProvider)
class ICurriculumGroup(IOptionalVideo, IAtlasProduct):

    __doc__ = "Curriculum Group"

class CurriculumGroup(Container):
    pass


# Base class for individual Curriculum
@provider(IFormFieldProvider)
class ICurriculum(IAtlasProduct):

    __doc__ = "Curriculum"

class Curriculum(Container):
    pass


# Simple Curriculum: Physical product
@provider(IFormFieldProvider)
class ICurriculumSimple(ICurriculum):

    __doc__ = "Curriculum (Simple)"

class CurriculumSimple(Curriculum):
    pass


# Digital Curriculum: Online/digital material
@provider(IFormFieldProvider)
class ICurriculumDigital(ICurriculum):

    __doc__ = "Curriculum (Digital)"

class CurriculumDigital(Curriculum):

    always_allowed = ['atlas_curriculum_instructions',]

    def allowedContentTypes(self):

        # Get existing allowed types
        allowed_content_types = super(CurriculumDigital, self).allowedContentTypes()

        allowed_content_type_ids = [x.getId() for x in allowed_content_types]

        # Once we've added content, restrict the content to just that type
        folder_contents = self.listFolderContents({'portal_type' : allowed_content_type_ids})

        # If the folder has existing contents
        if folder_contents:

            # Find types that are in the folder, but not 'always allowed'
            folder_contents_types = list(set([x.portal_type for x in folder_contents]) - set(self.always_allowed))

            if folder_contents_types:

                # Append the 'always_allowed' type(s) and return
                folder_contents_types.extend(self.always_allowed)
                return [x for x in allowed_content_types if x.getId() in set(folder_contents_types)]

        # Return default allowed types
        return allowed_content_types

# Instructions (contained in Curriculum Digital)
@provider(IFormFieldProvider)
class ICurriculumInstructions(IArticleDexterityContainedContent):

    __doc__ = "Curriculum Instructions"

class CurriculumInstructions(Container):
    pass

# Module (contained in Curriculum Digital)
@provider(IFormFieldProvider)
class ICurriculumModule(IArticleDexterityContainedContent):

    __doc__ = "Curriculum Module"

class CurriculumModule(Container):
    pass

# Lesson (contained in Curriculum Digital *or* Curriculum Module)
@provider(IFormFieldProvider)
class ICurriculumLesson(IArticleDexterityContainedContent):

    __doc__ = "Curriculum Lesson"

class CurriculumLesson(Container):
    pass