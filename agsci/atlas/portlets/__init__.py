from plone.app.portlets.portlets.navigation import Renderer as _NavigationRenderer
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class NavigationRenderer(_NavigationRenderer):
    _template = ViewPageTemplateFile('templates/navigation.pt')
    recurse = ViewPageTemplateFile('templates/navigation_recurse.pt')
