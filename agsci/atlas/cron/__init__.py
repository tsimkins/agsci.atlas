from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.registry.interfaces import IRegistry
from zope.component import getAdapters, getUtility
from zope.interface import Interface, alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse
from zope.security import checkPermission
from zLOG import INFO

from ..browser.views.sync.base import BaseImportContentView, IDisableCSRFProtection
from ..utilities import execute_under_special_role
from ..permissions import ATLAS_SUPERUSER

import transaction

class ICronJob(Interface):

    __doc__ = "All"

class ICronJobWeekly(ICronJob):

    __doc__ = "Weekly"

class ICronJobDaily(ICronJob):

    __doc__ = "Daily"

class ICronJobHourly(ICronJobDaily):

    __doc__ = "Hourly"

class ICronJobQuarterHourly(ICronJobHourly):

    __doc__ = "Quarter Hourly"

class ICronJobUnscheduled(ICronJob):

    __doc__ = "Unscheduled"

class ICronJobMagentoIntegration(ICronJob):

    __doc__ = "Magento Integration"

class ICronJobMagentoOffHoursIntegration(ICronJob):

    __doc__ = "Magento Off Hours Integration"

class ICronJobM2Integration(ICronJob):

    __doc__ = "M2 Integration"

@implementer(IPublishTraverse)
class CronJobView(BaseImportContentView):

    index = ViewPageTemplateFile("templates/cron.pt")

    schedule_interfaces = [
        ('quarter_hourly' , ICronJobQuarterHourly),
        ('hourly' , ICronJobHourly),
        ('daily' , ICronJobDaily),
        ('weekly' , ICronJobWeekly),
        ('unscheduled' , ICronJobUnscheduled),
        ('magento_integration', ICronJobMagentoIntegration),
        ('magento_off_hours_integration', ICronJobMagentoOffHoursIntegration),
        ('m2_integration', ICronJobM2Integration),
    ]

    @property
    def interfaces(self):
        return dict(self.schedule_interfaces)

    @property
    def schedules(self):
        return [x[0] for x in schedule_interfaces]

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.interval = None

        self.logs = []

        # Generated at call time.
        self.entry_id = self._entry_id

    def name(self):
        return '@@' + self.__name__

    @property
    def job_name(self):
        return self.request.form.get('job_name', None)

    # Log messages to Zope log and stdout
    def log(self, summary, severity=INFO, detail=''):
        super(CronJobView, self).log(summary, severity=severity, detail=detail)

        self.logs.append(summary)

        if detail:
            self.logs.append(detail)

    # Pull interval from view name
    def publishTraverse(self, request, name):

        if name:
            self.interval = name

        return self

    # This method is run when the view is called.
    def __call__(self):

        if self.adapter_interface:
            return self.run_jobs()

        # Render cron job listing if we're not calling anything.
        return self.index()

    # If a person is a superuser, allow run regardless of IP
    @property
    def is_superuser(self):
        return checkPermission(ATLAS_SUPERUSER, self.context)

    # Checks if jobs are allowed to run, and runs them.
    def run_jobs(self):

        # Check if the person is a superuser.  If they are, continue.  If not
        # validate the IP
        if not self.is_superuser:

            # Validate IP
            if not self.remoteIPAllowed():
                return self.HTTPError('IP "%s" not permitted to run cron jobs.' % self.remote_ip)

        # Override CSRF protection so we can make changes from a GET
        #
        # Controls:
        #   * Remote IP checked against ACL
        #   * UID checked for valid format via regex.
        #   * Importer class points to pre-determined URL for JSON data
        alsoProvides(self.request, IDisableCSRFProtection)

        # Set content type header
        self.request.response.setHeader('Content-Type', 'text/plain')

        self.log("Running %s Cron" % self.adapter_interface.__doc__)

        for job in self.jobs:

            _job = repr(job)

            # If we have an exception, return it in the HTTP response rather than
            # raising an exception
            try:
                # Running jobs as managerso we can do this anonymously.
                self.log("\nRunning Job '%s'" % _job)

                rv = execute_under_special_role(['Manager'], job._run)

                if rv:
                    self.log("\nJob Output")
                    self.log("-"*50)
                    self.log("\n".join(rv))
                    self.log("-"*50)

            except Exception as e:
                self.log("Failed Job '%s'" % _job)

                # TODO: Send email on failure

                self.log('%s: %s' % (type(e).__name__, e.message))

            else:
                self.log("Success Job '%s'" % _job)

            self.log("="*50)

        # Return the logs
        return "\n".join(self.logs)


    @property
    def adapter_interface(self):

        return self.interfaces.get(self.interval, None)

    @property
    def jobs(self):

        jobs = self.get_jobs(interface=self.adapter_interface, job_name=self.job_name)
        return [x[1] for x in jobs]


    def get_jobs(self, interface=None, job_name=None):

        jobs = []

        for (name, adapted) in getAdapters((self.context,), interface):
            # If a job name was provided (name="..." in configure.zcml)
            # only return that job.
            if job_name and job_name != name:
                continue

            jobs.append((name, adapted))

        jobs.sort(key=lambda x: x[1].priority)

        return jobs

class CronJob(object):

    title = "Generic Job"

    priority = 5

    enabled = True

    def __repr__(self):
        return self.title

    def __init__(self, context):
        self.context = context
        self.logs = []
        self.start = self.now

    def log(self, i):
        self.logs.append(i)

    def _run(self):

        if self.enabled:

            # Run the job
            _t = transaction.begin()

            try:
                self.run()
            except Exception as e:
                _t.abort()
                raise e
            else:
                _t.commit()

            # Set the end time
            self.end = self.now

            elapsed = self.end - self.start

            self.log("Elapsed time: %0.2f seconds" % (elapsed*86400))

        else:
            self.log("Job disabled.")

        # Return the job logs
        return self.logs

    def run(self):
        pass

    @property
    def now(self):
        return DateTime()

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal_workflow(self):
        return getToolByName(self.context, 'portal_workflow')

    @property
    def registry(self):
        return getUtility(IRegistry)
