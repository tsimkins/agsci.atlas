from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.DCWorkflow.interfaces import IBeforeTransitionEvent
from plone.registry.interfaces import IRegistry
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.lifecycleevent import IObjectModifiedEvent

import requests

from ..content import IAtlasProduct

# Returns the value of the Jitterbit Endpoint URL from the registry
def getUpdateEndpointURL():
    registry = getUtility(IRegistry)
    return registry.get('agsci.atlas.jitterbit.product_update_endpoint_url')

# Notify a Jitterbit Endpoint that something's been updated
def notify(context, event):

    states = ('published', 'expired')

    # If we're not a product, find our nearest parent product
    if not IAtlasProduct.providedBy(context):

        for o in context.aq_chain:

            if IAtlasProduct.providedBy(o):
                context = o
                break

            if IPloneSiteRoot.providedBy(o):
                break

    # Set up a request annotation for this object so it doesn't get sent twice.
    request = getRequest()

    key = u'NOTIFY_JITTERBIT_UIDS'
    cache = IAnnotations(request)

    if not cache.has_key(key):
        cache[key] = []

    # Skip if we've sent this already for this request
    if context.UID() in cache[key]:
        return

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
        request.form['bin'] = 'false'

        # set 'recursive' to False
        request.form['recursive'] = 'false'

        # set 'expensive' to False
        request.form['expensive'] = 'false'

        # Get the API data
        api_view = context.restrictedTraverse('@@api')

        # Stuff it into a structure similar to the main "updated" @@api call.
        data = {
            "contents" : [
                api_view.getData(),
            ],
        }

        # Post it to the url
        try:
            rv = requests.post(url, json=data, timeout=30)
        except requests.exceptions.RequestException, e:
            api_view.log(u"Error POST'ing update: %s %s" % (e.__class__.__name__, e.message))
        else:
            cache[key].append(context.UID())