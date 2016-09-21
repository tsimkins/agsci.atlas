from Acquisition import aq_chain
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName

import requests

API_OUTPUT_DIRECTORY = "/usr/local/plone-atlas/zeocluster/api"

JITTERBIT_URL = "http://example.com/post-test"

# Call to external system (Jitterbit?) when article is published.

def onArticlePublish(context, event):

    if event.action in ['publish', ]:

        # Get XML from @@api call to object
        try:
            v = context.restrictedTraverse("@@api")
        except AttributeError:
            # Couldn't find API view, swallow error
            return False

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


# If content is added, removed, moved (renamed) or edited, unpublish the parent
# article.

def onArticleContentCRUD(context, event):

    for o in aq_chain(event.object):
        if hasattr(o, 'Type'):
            if o.Type() in ['Article', ]:
                wftool = getToolByName(o, "portal_workflow")
                review_state = wftool.getInfoFor(o, 'review_state').lower()

                # If the article is in a Published state, retract
                if review_state in ['published', ]:
                    wftool.doActionFor(o, 'retract')
                    o.reindexObject()
                    o.reindexObjectSecurity() # Not sure if we need this

                else:
                    # Regardless, reindex the article so it recalculates the content checks
                    o.reindexObject(idxs=['ContentIssues',])
                    o.reindexObject(idxs=['ContentErrorCodes'])

                return True

    return False
