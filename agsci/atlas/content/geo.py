from plone.registry.interfaces import IRegistry
from z3c.form.browser import text
from z3c.form.converter import DecimalDataConverter
from z3c.form.interfaces import ITextWidget
from z3c.form.widget import FieldWidget
from zope.component import adapter, getUtility
from zope.interface import implementer_only
from zope.schema.interfaces import IDecimal

import decimal

from .. import AtlasMessageFactory as _

class ILatLngWidget(ITextWidget):
    pass

@implementer_only(ILatLngWidget)
class LatLngWidget(text.TextWidget):

    klass = u'geo-text-widget'

def LatLngFieldWidget(field, request):
    return FieldWidget(field, LatLngWidget(request))

class LatLngFormatter(object):

    default = decimal.Decimal(0.0)

    def __init__(self, _type):
        self.type = _type

    def format(self, value):
        if isinstance(value, decimal.Decimal):
            return value.quantize(decimal.Decimal('.00000001'), rounding=decimal.ROUND_DOWN)

        return self.default

    def parse(self, value):
        try:
            return decimal.Decimal(value)
        except:
            return self.default

@adapter(IDecimal, ILatLngWidget)
class LatLngDataConverter(DecimalDataConverter):

    type = decimal.Decimal

    errorMessage = _('The entered value is not a valid decimal literal.')

    def __init__(self, field, widget):
        super(DecimalDataConverter, self).__init__(field, widget)
        self.formatter = LatLngFormatter(self.type)


# This takes a Plone object, and returns various lat/lng related data
class LocationAdapter(object):

    def __init__(self, context):
        self.context = context

    @property
    def latitude(self):
        return getattr(self.context, 'latitude', None)

    @property
    def longitude(self):
        return getattr(self.context, 'longitude', None)

    @property
    def coords(self):
        return (self.latitude, self.longitude)

    @property
    def has_coords(self):
        return not (isinstance(self.latitude, type(None)) or isinstance(self.longitude, type(None)))

    @property
    def has_valid_coords(self):

        if self.has_coords:
            return not (self.latitude == 0 or self.longitude == 0)

        return False

    @property
    def api_key(self):
        registry = getUtility(IRegistry)
        return registry.get('agsci.atlas.google_maps_api_key')