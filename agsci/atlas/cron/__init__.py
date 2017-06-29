from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getAdapters
from zope.interface import Interface, alsoProvides, implements
from zope.publisher.interfaces import IPublishTraverse

from ..browser.views.sync.base import BaseImportContentView, IDisableCSRFProtection
from ..utilities import execute_under_special_role

import transaction

class ICronJob(Interface):

    __doc__ = "All"

class ICronJobQuarterHourly(ICronJob):

    __doc__ = "Quarter Hourly"

class ICronJobHourly(ICronJob):

    __doc__ = "Hourly"

class ICronJobDaily(ICronJob):

    __doc__ = "Daily"

class ICronJobWeekly(ICronJob):

    __doc__ = "Weekly"

class CronJobView(BaseImportContentView):

    implements(IPublishTraverse)

    index = ViewPageTemplateFile("templates/cron.pt")

    schedule_interfaces = [
        ('quarter_hourly' , ICronJobQuarterHourly),
        ('hourly' , ICronJobHourly),
        ('daily' , ICronJobDaily),
        ('weekly' , ICronJobWeekly),
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
    def log(self, summary, detail=''):
        super(CronJobView, self).log(summary, detail=detail)

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

    def run_jobs(self):

        # Validate IP
        if not self.remoteIPAllowed():
            return self.HTTPError('IP "%s" not permitted to run cron jobs.' % self.remote_ip)

        # Any additional request validation
        try:
            if not self.requestValidation():
                return self.HTTPError('Request validation failed.')
        except Exception as e:
            return self.HTTPError(e.message)

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

        jobs.sort(key=lambda x: x[1].priority, reverse=True)

        return jobs

class CronJob(object):

    title = "Generic Job"

    priority = 5

    def __repr__(self):
        return self.title

    def __init__(self, context):
        self.context = context
        self.logs = []
        self.start = self.now

    def log(self, i):
        self.logs.append(i)

    def _run(self):
        # Run the job
        _t = transaction.begin()

        try:
            self.run()
        except Exception, e:
            _t.abort()
            raise e
        else:
            _t.commit()

        # Set the end time
        self.end = self.now

        elapsed = self.end - self.start

        self.log("Elapsed time: %0.2f seconds" % (elapsed*86400))

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