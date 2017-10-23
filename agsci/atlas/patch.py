from Acquisition import aq_inner
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFDiffTool.BaseDiff import BaseDiff
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from plone.dexterity.browser.edit import DefaultEditForm
from zope.globalrequest import getRequest

# This patch adds an 'update' method to the EventAccessor class.  The 'edit`
# method of this class only updates values in **kwargs that are in the
# _behavior_map dict.  The purpose of this method is to set the attribute value
# for anything that's *not* in that dict.

def event_accessor_update(self, **kwargs):

    bm = self._behavior_map

    for key, value in kwargs.items():
        if key not in bm:
            setattr(self.context, key, value)

    notify(ObjectModifiedEvent(self.context))

# From Products.CMFDiffTool.dexteritydiff.DexterityCompoundDiff._compute_fields_order
# Patching in from v3.0.4 (2016-02-27)

def patched_compute_fields_order(self, obj):
    form = DefaultEditForm(obj, getRequest())
    form.portal_type = obj.portal_type
    form.updateFields()
    all_fields = list()
    all_fields += [(form.fields[name].field, name) for name in form.fields]
    if form.groups:
        for group in form.groups:
            all_fields += [(group.fields[name].field, name) for name in group.fields]

    return all_fields

# Patch to Products.CMFDiffTool.ListDiff so a list field with a value of None returns an empty list instead.
def ListDiff_parseField(self, value, filename=None):
    """Parse a field value in preparation for diffing"""
    # Return the list as is for diffing
    if type(value) is set:
        # A set cannot be indexed, so return a list of a set
        return list(value)
    else:
        if value is None:  # Patched
            return []      # Patched
        return value

def eea_facetednavigation_widgets_sorting_vocabulary(self, **kwargs):
    """ Return data vocabulary
    """
    vocab = self.portal_vocabulary()
    sort_fields = [x for x in self.listSortFields()]

    if not vocab:
        return sort_fields

    vocab_fields = [(x[0], x[1], '') for x in vocab]
    sort_field_ids = [x[0] for x in sort_fields]

    return [f for f in vocab_fields if f[0] in sort_field_ids]

def patched_visibleToRole(published, role, permission='View'):
    return True

# Patch 'plone.app.caching.operations.utils.visibleToRole' to it always returns True
# Do it the old fashioned way
from plone.app.caching.operations import utils
utils.visibleToRole = patched_visibleToRole

# Stolen from `toLocalizedTime` in agsci.UniversalExtender.patch
def toLocalizedTime(self, time, long_format=None, time_only=None, end_time=None):
    """Convert time to localized time
    """

    context = aq_inner(self.context)
    util = getToolByName(context, 'translation_service')

    def friendly(d):

        if not d:
            return ''

        if d.startswith('0'):
            d = d.replace('0', '', 1)

        d = d.replace('12:00 AM', '').strip()

        return d.replace(' 0', ' ')

    # Converts a timestamp to a DateTime object.
    # If it's a GMT time, convert that to US/Eastern
    def toDateTime(t):

        if not isinstance(t, DateTime):
            t = DateTime(t)

        if t.timezone() == 'GMT+0':
            t = t.toZone('US/Eastern')

        return t

    if not time:
        return ''

    # Handle error when converting invalid times.

    try:
        start_full_fmt = friendly(util.ulocalized_time(time, long_format, time_only, context=context,
                                  domain='plonelocales', request=self.request))
    except ValueError:
        return ''

    if end_time:
        try:
            end_full_fmt = friendly(util.ulocalized_time(end_time, long_format, time_only, context=context,
                                    domain='plonelocales', request=self.request))
        except ValueError:
            return ''

        start = toDateTime(time)
        end = toDateTime(end_time)

        start_date_fmt = start.strftime('%Y-%m-%d')
        end_date_fmt = end.strftime('%Y-%m-%d')

        start_time_fmt = start.strftime('%H:%M')
        end_time_fmt = end.strftime('%H:%M')

        # If the same date
        if start_date_fmt == end_date_fmt:

            # If we want the long format, return [date] [time] - [time]
            if long_format:
                if start_time_fmt == end_time_fmt:
                    return start_full_fmt
                elif start_time_fmt == '00:00':
                    return end_full_fmt
                elif end_time_fmt == '00:00':
                    return start_full_fmt
                else:
                    return '%s, %s - %s' % (self.toLocalizedTime(time), self.toLocalizedTime(time, time_only=1), self.toLocalizedTime(end_time, time_only=1))
            # if time_only
            elif time_only:
                if start_full_fmt and end_full_fmt:
                    if start_full_fmt == end_full_fmt:
                        return start_full_fmt
                    else:
                        return '%s - %s' % (start_full_fmt, end_full_fmt)
                elif start_full_fmt:
                    return start_full_fmt
                elif end_full_fmt:
                    return end_full_fmt
                else:
                    return ''
            # Return the start date in short format
            else:
                return start_full_fmt
        else:
            default_repr = '%s to %s' % (friendly(start_full_fmt), friendly(end_full_fmt))
            if long_format:
                return default_repr
            elif time_only:
                if start_full_fmt and end_full_fmt:
                    if start_full_fmt == end_full_fmt:
                        return start_full_fmt
                    else:
                        return '%s - %s' % (start_full_fmt, end_full_fmt)
                elif start_full_fmt:
                    return start_full_fmt
                elif end_full_fmt:
                    return end_full_fmt
                else:
                    return ''
            elif start.year() == end.year():
                if start.month() == end.month():
                    return '%s %d-%d, %d' % (start.strftime('%B'), start.day(), end.day(), start.year())
                else:
                    return '%s %d - %s %d, %d' % (start.strftime('%B'), start.day(), end.strftime('%B'), end.day(), start.year())
            else:
                return default_repr

    else:
        if start_full_fmt:
            return friendly(start_full_fmt)
        else:
            return ''

# Patches for history diff.  Swallowing errors, and giving what we can.
def FieldDiff_getLineDiffs(self):
    a = self._parseField(self.oldValue, filename=self.oldFilename)
    b = self._parseField(self.newValue, filename=self.newFilename)

    try:
        return super(self, FieldDiff).getLineDiffs()
    except TypeError:
        return []

class NOOPDiff(BaseDiff):

    def __init__(self, obj1, obj2, field, id1=None, id2=None,
                 field_name=None, field_label=None,schemata=None):
        self.field = field
        self.oldValue = ''
        self.newValue = ''
        self.same = True
        self.id1 = ''
        self.id2 = ''
        self.label = field_label or field
        self.schemata = schemata or 'default'

def DexterityCompoundDiff__diff_field(self, obj1, obj2, field, schema_name):

    diff_type = self._get_diff_type(field)

    try:

        return diff_type(
            obj1,
            obj2,
            field.getName(),
            id1=self.id1,
            id2=self.id2,
            field_name=field.getName(),
            field_label=field.title,
            schemata=schema_name
        )
    except AttributeError:

        return NOOPDiff(
            obj1,
            obj2,
            field.getName(),
            id1=self.id1,
            id2=self.id2,
            field_name=field.getName(),
            field_label=field.title,
            schemata=schema_name
        )