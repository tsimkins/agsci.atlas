import requests
from DateTime import DateTime

API_OUTPUT_DIRECTORY = "/usr/local/plone-atlas/zeocluster/api"

JITTERBIT_URL = "http://example.com/post-test"

# Call to external system (Jitterbit?) when article is published.

def onArticlePublish(context, event):

    if event.action in ['publish', ]:
    
        # Get XML from @@api call to object
        v = context.restrictedTraverse("@@api")
        xml = v()

        # For now, just rendering the API view and dumping to temporary location
        now = DateTime().strftime('%Y%m%d_%H%M%S')
        
        filename = "_".join([context.UID(), event.action, now])
        
        output = open("%s/%s.xml" % (API_OUTPUT_DIRECTORY, filename), "w")
        output.write(xml)
        output.close()

        # POST data to Jitterbit
        post_data = {'foo' : 'bar'}
        response = requests.post(JITTERBIT_URL, data=post_data)

        # Response, status etc
        response.text
        response.status_code

        return True
    
    return False

