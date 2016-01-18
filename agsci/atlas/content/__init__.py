from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from plone.supermodel import model

# Hierarchy of metadata
metadata_content_types = ['Category', 'Program', 'Topic']
required_metadata_content_types = ['Category', 'Program']

def getMetadataByContentType(context, content_type):

    if content_type not in metadata_content_types:
        return None

    filtered_metadata_content_types = metadata_content_types[0:metadata_content_types.index(content_type)+1]

    v = {}

    for o in context.aq_chain:

        if IPloneSiteRoot.providedBy(o):
            break

        if hasattr(o, 'Type') and hasattr(o.Type, '__call__'):
            if o.Type() in metadata_content_types:
                v[o.Type()] = o.Title()
        else:
            break

    if v.has_key(content_type):
        return ':'.join([v.get(x) for x in filtered_metadata_content_types if v.has_key(x)])

    return None
    
# Parent class for all article content.  Used to indicate a piece of  
# Dexterity content used in an article.  This interface allows us to
# trigger workflow on CRUD of article content types.

class IArticleDexterityContent(model.Schema):

    pass