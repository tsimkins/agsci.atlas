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

def eea_facetednavigation_widgets_sorting_vocabulary(self, **kwargs):
        """ Return data vocabulary
        """
        vocab = self.portal_vocabulary()
        sort_fields = [x for x in self.listSortFields()]

        if not vocab:
            return sort_fields

        vocab_fields = [field[0].replace('term.', '', 1) for field in vocab]
        sort_field_ids = [x[0] for x in sort_fields]

        def fixVocab(x):
            y = list(x)
            y.append(x[-1])
            return tuple(y)

        return [fixVocab(f) for f in vocab if f[0] in sort_field_ids]