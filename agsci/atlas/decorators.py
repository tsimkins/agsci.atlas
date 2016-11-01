from functools import wraps
from datetime import datetime
from zLOG import LOG
from zope.globalrequest import getRequest
from zope.annotation.interfaces import IAnnotations

# This is a decorator (@context_memoize) that memoizes no-parameter methods based
# on the method name and UID for the context. The purpose is to not have to call
# ".html", ".text", ".soup", etc. many times for many different checks.
#
# Rudimentary tracking shows a 30% increase in performance, which will be more
# apparent as we're running more checks.

def context_memoize(func):

    @wraps(func)
    def func_wrapper(name):
        key = getKey(func, name)
        return getCachedValue(func, key, name)

    def getKey(func, name):
        uid = name.context.UID()
        method = func.__name__
        return '-'.join([method, uid])

    def getCachedValue(func, key, name):
        request = getRequest()

        cache = IAnnotations(request)

        if not cache.has_key(key):
            cache[key] = func(name)

        return cache[key]

    return func_wrapper

# Logs the time for the function to run, used for debugging.
def log_time(func):

    @wraps(func)
    def func_wrapper(name):

        check_name = name.title

        s0 = datetime.now()

        v = func(name)

        s1 = datetime.now()

        time_diff = (s1-s0).total_seconds()

        LOG('ContentCheck: |%s|' % check_name, LOG, '|%0.4f| seconds' % time_diff)

        return v

    return func_wrapper