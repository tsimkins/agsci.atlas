# Active review states (not archived, expired, etc.)
ACTIVE_REVIEW_STATES = ['requires_initial_review', 'pending', 'published',
                        'expiring_soon', 'requires_feedback',  'private']

# Catalog Visibility
V_CS = 'Catalog, Search'
V_C = 'Catalog'
V_NVI = 'Not Visible Individually'

# Naively assume that all dates are in Eastern time
DEFAULT_TIMEZONE = 'US/Eastern'

# Delimiter for categories/teams
DELIMITER = '|'

# Mimetype to PIL and filename extension
IMAGE_FORMATS = {
    'image/jpeg' : ['JPEG', 'jpg'],
    'image/png' : ['PNG', 'png'],
    'image/gif' : ['GIF', 'gif'],
    'image/x-ms-bmp' : ['BMP', 'bmp'],
}