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