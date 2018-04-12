from Products.CMFCore.WorkflowCore import WorkflowException
import requests
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from Products.CMFCore.utils import getToolByName

from zope.lifecycleevent import IObjectModifiedEvent
from Products.DCWorkflow.interfaces import IBeforeTransitionEvent

# Returns the value of the Jitterbit Endpoint URL from the registry
def getUpdateEndpointURL():
    registry = getUtility(IRegistry)
    return registry.get('agsci.atlas.jitterbit.product_update_endpoint_url')

def notify(context, event):

    states = ('published', 'expired')

    # Check to see if the current workflow state of theobject is published or expired
    if IObjectModifiedEvent.providedBy(event):
        wftool = getToolByName(context, "portal_workflow")

        try:
            review_state = wftool.getInfoFor(context, 'review_state').lower()
        except WorkflowException:
            review_state = ''

        if review_state not in states:
            return # Not published or expired

    # Check if we're transitioning to that state
    elif IBeforeTransitionEvent.providedBy(event):

        if event.new_state.getId() not in states:
            return # Not published or expired

    url = getUpdateEndpointURL()

    if url:

        # set 'bin' to False
        context.REQUEST.form['bin'] = 'false'

        # set 'recursive' to False
        context.REQUEST.form['recursive'] = 'false'

        # Get the API data
        api_view = context.restrictedTraverse('@@api')
        data = api_view.getData()

        # Post it to the url
        try:
            rv = requests.post(url, json=data, timeout=30)
        except requests.exceptions.RequestException, e:
            api_view.log(u"Error POST'ing update: %s %s" % (e.__class__.__name__, e.message))