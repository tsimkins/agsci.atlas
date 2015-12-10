from agsci.atlas import AtlasMessageFactory as _
from article import IArticlePage
from plone.supermodel import model
from urlparse import urlparse, parse_qs
from zope import schema
from zope.component import adapter
from zope.interface import provider, implementer
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from ..interfaces import IVideoMarker

video_providers = SimpleVocabulary(
    [SimpleTerm(value=x.lower(), title=_(x)) for x in (u'YouTube', u'Vimeo')]
    )

class IVideo(IArticlePage):

    link = schema.TextLine(
        title=_(u"Video Link"),
        required=True,
    )
    
    provider = schema.Choice(
        title=_(u"Video Provider"),
        vocabulary=video_providers,
        required=True,
    )

@adapter(IVideo)
@implementer(IVideoMarker)
class Video(object):

    def __init__(self, context):
        self.context = context

    def getVideoProvider(self):
        return getattr(self.context, 'provider', None)

    def getVideoId(self):
    
        url = getattr(self.context, 'link', None)
        provider = self.getVideoProvider()
        
        if url and provider:

            url_object = urlparse(url)
            url_site = url_object.netloc
            
            # YouTube - grab the 'v' parameter
            
            if provider == 'youtube' or url_site.endswith('youtube.com'):

                params = parse_qs(url_object.query)

                v = params.get('v', None)
                
                if v:
                    if isinstance(v, list):
                        return v[0]
                    else:
                        return v

            # Vimeo - grab the first URl segent
            if provider == 'vimeo' or url_site.endswith('vimeo.com'):
            
                url_path = url_object.path
                
                return url_path.split('/')[1]
            
        return None