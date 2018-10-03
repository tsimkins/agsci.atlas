from Products.CMFCore.utils import getToolByName
from datetime import date
from plone.app.z3cform.widget import DatetimeFieldWidget as _DatetimeFieldWidget
from plone.formwidget.datetime.z3cform.widget import DatetimeWidget as _DatetimeWidget

import z3c.form

class DatetimeWidget(_DatetimeWidget):

    @property
    def years_range(self):

        # Stolen from collective.z3cform.datetimewidget.widget_date.DateWidget

        portal_properties = getToolByName(self.context, 'portal_properties', None)

        if portal_properties is not None:
            p = portal_properties['site_properties']
        else:
            p = None

        today = date.today()

        if self.field.min is not None:
            start = self.field.min.year - today.year
        else:
            calendar_starting_year = getattr(p, 'calendar_starting_year', 2001)
            start = calendar_starting_year - today.year

        if self.field.max is not None:
            end = self.field.max.year - today.year
        else:
            end = getattr(p, 'calendar_future_years_available', 5)

        return (start, end)

def DatetimeFieldWidget(field, request):
    return z3c.form.widget.FieldWidget(field, DatetimeWidget(request))