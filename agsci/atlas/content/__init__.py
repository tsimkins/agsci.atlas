from plone.supermodel import model
from plone.dexterity.content import Container as _Container

# Parent class for all article content.  Used to indicate a piece of  
# Dexterity content used in an article.  This interface allows us to
# trigger workflow on CRUD of article content types.

class IArticleDexterityContent(model.Schema):

    pass
    
class Container(_Container):

    page_types = []
    
    def getPages(self):

        pages = self.listFolderContents({'Type' : self.page_types})
        
        return pages