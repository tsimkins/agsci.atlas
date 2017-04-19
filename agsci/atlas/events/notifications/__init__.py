from Products.CMFCore.utils import getToolByName
from plone.app.contentrules.actions.mail import MailAction, MailActionExecutor
from plone.app.layout.viewlets.content import ContentHistoryView
from agsci.atlas.utilities import SitePeople
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.globalrequest import getRequest
from zLOG import LOG, INFO, ERROR

import textwrap

# Notification config object.  It's just easier this way.
class NotificationConfiguration(object):

    # Hardcoded sender
    SENDER="Extension CMS <do.not.reply@psu.edu>"

    # Hardcoded subject prefix
    SUBJECT_PREFIX = "Extension Content Alert"

    # Format for products submitted for review
    SUBMIT_FORMAT = textwrap.dedent("""
    ${user_fullname} submitted a product for review by the web team.

    ${type} Information:

        Title: ${title}
        Description: ${description}
        URL: ${url}

    Please review and either publish, or return to owner for feedback.
    """).strip()

    # Format for products returned with feedback
    FEEDBACK_FORMAT = textwrap.dedent("""
    The web team has reviewed the ${type} you submitted:

        Title: ${title}
        Description: ${description}
        URL: ${url}

    and provided the following feedback:

    ----------------------------------------------------------------------------
    ${change_comment}
    ----------------------------------------------------------------------------

    Please review, address any issues, and re-submit for publication.
    """).strip()

    def __init__(self, context=None, event=None):
        self.context = context
        self.event = event
        self.request = getRequest()

    # Plone Registry
    @property
    def registry(self):
        return getUtility(IRegistry)

    # Is the notification system enabled?
    @property
    def enabled(self):
        return not not self.registry.get('agsci.atlas.notification_enable')

    # Is the notification system in debug mode?
    @property
    def debug(self):
        return not not self.registry.get('agsci.atlas.notification_debug')

    # Returns the configured debug email. If no email is configured, return a bogus one.
    @property
    def debug_email(self):

        debug_email = self.registry.get('agsci.atlas.notification_debug_email')

        if debug_email:
            return debug_email

        # Bogus email address
        return self.SENDER

    # Returns the configured web team email. If no email is configured, return a bogus one.
    @property
    def web_team_email(self):

        web_team_email = self.registry.get('agsci.atlas.notification_web_team_email')

        if web_team_email:
            return web_team_email

        return self.SENDER

    # Returns the current logged in user's id
    @property
    def current_user(self):

        portal_membership = getToolByName(self.context, 'portal_membership')
        member = portal_membership.getAuthenticatedMember()

        if member:
            return member.getId()

    # The most recent person that submitted the product for review
    @property
    def previous_submitter(self):

        # Get the history data
        history_view = ContentHistoryView(self.context, self.request)
        workflow_history = history_view.workflowHistory()

        # Pull the people who submitted this
        people = [x.get('actor', {}).get('username', None) for x in workflow_history if x.get('action', '') == 'submit']

        # Filter empties
        people = [x for x in people if x]

        # Return the most recent one, if we have people
        if people:
            return people[0]

    # Get the email addresses from the person ids
    def email_addresses(self, ids=[]):

        # Site People utility
        sp = SitePeople()

        # Get their person object
        brains = [sp.getPersonById(x) for x in ids]

        # Filter out people not found
        objects = [x.getObject() for x in brains if x]

        # Get their emails if it exists
        emails = [x.email for x in objects if x.email]

        # Return
        return emails

    # Returns all valid emails for the owner, author, and current user.
    @property
    def owner_email(self):

        # Empty List
        ids = []

        # Add the person that submitted the product for review to the list of owners.
        ids.append(self.previous_submitter)

        # Populate with owners and authors
        for i in ('owners', 'authors'):
            j = getattr(self.context, i, [])

            if j:
                ids.extend(j)

        # Email address lookup
        emails = self.email_addresses(ids)

        # If we have a list of people to email, join with ',' and return
        # We should always have at least the logged-in user, but if for some
        # reason we don't, it falls back to the debug em
        if emails:
            return ",".join(set(emails))

    # Send an email using the "MailAction/MailActionExecutor" method,
    # which interpolates ${...} variables.
    # Also includes logging.
    def send_mail(self, recipients='', subject='', message=''):

        msg = MailAction()

        msg.source = self.SENDER

        # If we're in debug mode, the email goes to the configured debug email.
        # Or, if we don't have recipients
        if self.debug or not recipients:
            msg.recipients = self.debug_email
        else:
            msg.recipients = recipients

        msg.subject = "%s: %s" % (self.SUBJECT_PREFIX, subject)
        msg.message = message

        # If we're in debug mode, log the message
        if self.debug:
            self.log(summary="DEBUG: Send email %s to %s" % (msg.subject, recipients))

        # Send the email and log error
        try:
            m = MailActionExecutor(self.context, msg, self.event)
            m()
        except:
            self.log(summary="Error sending email %s to %s" % (msg.subject, msg.recipients),
                     severity=ERROR)

    # Writes a message to the log
    def log(self, summary, severity=INFO, detail=''):
        subsystem = 'agsci.atlas.notifications'
        LOG(subsystem, severity, summary, detail)


# Handle notifications for workflow events
def notifyOnProductWorkflow(context, event):

    notify = NotificationConfiguration(context, event)

    # If the notification system is not enabled, stop processing
    if not notify.enabled:
        return

    # If no workflow action is provided on the event, we
    if not hasattr(event, 'action'):
        return

    # User submits content for review
    if event.action in ('submit'):
        notify.send_mail(recipients=notify.web_team_email,
                          subject=u"%s Review" % context.Type(),
                          message=notify.SUBMIT_FORMAT)

    # Web Team returns content with feedback
    elif event.action in ('requires_feedback',):
        notify.send_mail(recipients=notify.owner_email,
                          subject=u"%s Feedback Required" % context.Type(),
                          message=notify.FEEDBACK_FORMAT)