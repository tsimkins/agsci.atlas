from decimal import Decimal, ROUND_DOWN
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import googlemaps


# Returns the value of the API key from the registry
def getAPIKey():
    registry = getUtility(IRegistry)
    return registry.get('agsci.atlas.google_maps_api_key')

# Actions taken when an object with a location is saved
def onLocationProductCreateEdit(context, event, force=False):

    # Get attributes from object
    lat = getattr(context, 'latitude', None)
    lng = getattr(context, 'longitude', None)

    # Check if they're both non-null
    has_lat_lng = not (isinstance(lat, type(None)) or isinstance(lng, type(None)))

    # If we're forcing, or if we don't have values, get them and set them on the
    # object.
    if force or not has_lat_lng:

        (lat, lng) = getLatLng(context)

        setattr(context, 'latitude', lat)
        setattr(context, 'longitude', lng)

        context.reindexObject()


# Given an object that implements IAtlasLocation, do a Google Maps API lookup
# based on the address.  If no lat/lon is found, return (0,0)
def getLatLng(context):

    # Get the API key from the registry
    google_api_key = getAPIKey()

    # If we have a key, grab the address of the object, and query Google
    if google_api_key:

        # Get the full address of the location.  Ends up as comma-joined string
        # using all the fields found.

        # Street address
        address = getattr(context, 'street_address', '')

        if address and isinstance(address, (list, tuple)):
            address = [x.strip() for x in address if x.strip()]
            address = ", ".join(address)
        else:
            address = ''

        # City, State, ZIP Code
        (city, state, zip_code) = [
                                    getattr(context, x, '') for x in
                                    ('city', 'state', 'zip_code')
                                  ]

        # Full address
        full_address = [x for x in (address, city, state, zip_code) if x]
        full_address = [x.strip() for x in full_address if x.strip()]
        full_address = ", ".join(full_address)

        # Failsafe check: If we don't have a city, don't run the API call.
        if city:

            # Get a client and run the API call
            client = googlemaps.Client(google_api_key)
            results = client.geocode(full_address)

            # Iterate through results (if any) and return the first match for
            # lat and lng
            for r in results:
                location = r.get('geometry', {}).get('location', {})
                lat = location.get('lat', '')
                lng = location.get('lng', '')
                if lat and lng:

                    # Decimal to 8 places
                    lat = Decimal(lat).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)
                    lng = Decimal(lng).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)

                    return (lat, lng)

    return (0.0, 0.0)