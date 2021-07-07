from Products.CMFCore.utils import getToolByName
from datetime import date
from plone.app.z3cform.widget import DatetimeFieldWidget as _DatetimeFieldWidget
from plone.formwidget.datetime.z3cform.widget import DatetimeWidget as _DatetimeWidget

import pkg_resources
import z3c.form

# This fix was superseded in a later version of plone.formwidget.datetime
dist = pkg_resources.get_distribution("plone.formwidget.datetime")

if dist.version < '1.3.4':

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

else:

    class DatetimeWidget(_DatetimeWidget):
        pass

def DatetimeFieldWidget(field, request):
    return z3c.form.widget.FieldWidget(field, DatetimeWidget(request))
