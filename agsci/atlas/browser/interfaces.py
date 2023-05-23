try:
    from plonetheme.sunburst.browser.interfaces import IThemeSpecific as _IThemeSpecific
except ImportError:
    from plone.theme.interfaces import IDefaultPloneLayer as _IThemeSpecific

class IThemeSpecific(_IThemeSpecific):
    """Marker interface that defines a Zope 3 skin layer bound to a Skin
       Selection in portal_skins.
    """
