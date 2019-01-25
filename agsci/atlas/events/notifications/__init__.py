from Products.CMFCore.utils import getToolByName
from plone.app.contentrules.actions.mail import MailAction, MailActionExecutor
from plone.app.layout.viewlets.content import ContentHistoryView
from agsci.atlas.permissions import ATLAS_SUPERUSER, ATLAS_DIRECT_PUBLISH
from agsci.atlas.utilities import SitePeople
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.security import checkPermission
from zope.security.interfaces import NoInteraction
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

    # Format for items published without review by web team
    DIRECT_PUBLISH_FORMAT = textwrap.dedent("""
    The following ${type} has been published directly by ${user_fullname}:

        Title: ${title}
        Description: ${description}
        URL: ${url}

    """).strip()

    # Format for items published that will notify the Team Marketing Coordinators
    TMC_PUBLISH_FORMAT = textwrap.dedent("""

    The following ${type} has been published:

        Title: ${title}
        Description: ${description}
        URL: ${url}

    You are receiving this email because you are the Team Marketing Coordinator
    for the EPAS Unit selected on this content.

    """).strip()

    def __init__(self, context=None, event=None):
        self.context = context
        self.event = event

    @property
    def request(self):
        return getRequest()

    # Plone Registry
    @property
    def registry(self):
        return getUtility(IRegistry)

    # Portal Catalog
    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

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

    # Get the list of ids
    def getPeople(self, field):

        v = getattr(self.context, field, [])

        if v:
            return v

        return []

    # Owner ids
    @property
    def owners(self):
        return self.getPeople('owners')

    # Author ids
    @property
    def authors(self):
        return self.getPeople('authors')

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
    def feedback_email(self):

        # Empty List
        ids = []

        # Add the person that submitted the product for review to the list of owners.
        ids.append(self.previous_submitter)

        # Populate with owners
        ids.extend(self.owners)

        # Email address lookup
        emails = self.email_addresses(ids)

        # If we have a list of people to email, join with ',' and return
        # We should always have at least the logged-in user.
        if emails:
            return ",".join(set(emails))

    # Emails for Team Marketing Coordinators responsible for product

    def get_epas_unit(self, context):
        _ = getattr(context, 'epas_unit', [])

        if _ and isinstance(_, (list, tuple)):
            return _

        return []


    @property
    def tmc_email(self):

        rv = []

        context_epas_unit = self.get_epas_unit(self.context)

        if context_epas_unit:

            for r in self.tmc:

                o = r.getObject()
                o_epas_unit = self.get_epas_unit(o)

                if set(o_epas_unit) & set(context_epas_unit):
                    email = getattr(o, 'email', None)
                    if email:
                        rv.append(email)

        return ",".join(rv)

    # Team Marketing Coordinator People
    @property
    def tmc(self):
        sp = SitePeople(active=False)
        return sp.tmc

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

    try:
        can_direct_publish = checkPermission(ATLAS_DIRECT_PUBLISH, context)
    except NoInteraction:
        can_direct_publish = True

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
        notify.send_mail(recipients=notify.feedback_email,
                         subject=u"%s Feedback Required" % context.Type(),
                         message=notify.FEEDBACK_FORMAT)

    # User submits content for review
    elif event.action in ('publish'):

        tmc_email = notify.tmc_email

        if tmc_email:
            notify.send_mail(recipients=tmc_email,
                             subject=u"%s Published" % context.Type(),
                             message=notify.TMC_PUBLISH_FORMAT)

        if not can_direct_publish:
            notify.send_mail(recipients=notify.web_team_email,
                             subject=u"%s Directly Published" % context.Type(),
                             message=notify.DIRECT_PUBLISH_FORMAT)