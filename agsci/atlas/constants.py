from decimal import Decimal

# Active review states (not expired, etc.)
ACTIVE_REVIEW_STATES = [
    'pending',
    'published',
    'expiring_soon',
    'requires_feedback',
    'private',
]

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

# File extensions lookup hardcoded, so we don't have to use mimetypes_registry
MIMETYPE_EXTENSIONS = {
    u'application/pdf': u'pdf',
    u'application/vnd.ms-excel': u'xls',
    u'application/vnd.ms-excel.sheet.macroEnabled.12': u'xlsm',
    u'application/vnd.ms-powerpoint': u'ppt',
    u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': u'xlsx',
    u'application/vnd.openxmlformats-officedocument.wordprocessingml.document': u'docx',
    u'image/gif': u'gif',
    u'image/jpeg': u'jpg',
    u'image/png': u'png',
}

# Internal and External Store Names
INTERNAL_STORE_NAME = u'PSU Internal'
EXTERNAL_STORE_NAME = u'Penn State Extension'

# Internal Store Category Level 1
INTERNAL_STORE_CATEGORY_LEVEL_1 = 'Penn State Extension Internal Store'

# Values that are false/null, but not empty
ALLOW_FALSE_VALUES = (int, bool, Decimal, float)

# API Domain for CMS site
CMS_DOMAIN="r39JxvLi.cms.extension.psu.edu"