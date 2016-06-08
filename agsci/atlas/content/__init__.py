from plone.supermodel import model
    
# Parent class for all article content.  Used to indicate a piece of  
# Dexterity content used in an article.  This interface allows us to
# trigger workflow on CRUD of article content types.

class IArticleDexterityContent(model.Schema):

    pass