from decimal import Decimal

import re

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
V_S = 'Search'

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

# Tools domain
TOOLS_DOMAIN="tools.agsci.psu.edu"

# Magento Data JSON URLs
MAGENTO_DATA_URL = "http://%s/m2.json" % CMS_DOMAIN
MAGENTO_CATEGORIES_URL = "http://%s/magento/categories.json" % CMS_DOMAIN

# Initial Date for Google Analytics Data
GA_START_DATE='2017-10'

# API Image Settings
API_IMAGE_QUALITY = 88
API_IMAGE_WIDTH = 900.0

# YouTube Channels
EXTENSION_YOUTUBE_CHANNEL_ID = 'UCJBLYNMZSQQrotFPzrv6I7A'
COLLEGE_YOUTUBE_CHANNEL_ID = 'UCKNxhWl61jLdxmxjNFntVzA'


# Review Period in years by content type
REVIEW_PERIOD_YEARS = {
    'Article' : 3,
    'News Item' : 1,
    'Learn Now Video' : 3,
    'Webinar' : 1,
    'App' : 3,
    'Smart Sheet' : 3,
    'Learn Now Video Series' : 3,
}

# Notification period (months)
REVIEW_PERIOD_NOTIFY = {}

for (k,v) in REVIEW_PERIOD_YEARS.items():
    if v not in REVIEW_PERIOD_NOTIFY:
        REVIEW_PERIOD_NOTIFY[v] = []
    REVIEW_PERIOD_NOTIFY[v].append(k)

# ADPs

EPAS_UNIT_LEADERS = {
    '4-H Youth Development': ['jur418', ], # Rice, Joshua E.
    'Agronomy and Natural Resources': ['cdh13', ], # Houser, Chris
    'Animal Systems': ['anl113', ], # Yutzy, Amber
    'Energy, Business, and Community Vitality': ['jrl110', ], # Ladlee, James R.
    'Food Safety and Quality': ['cnc3', ], # Cutter, Catherine Nettles
    'Food, Families, and Health': ['eag107', ], # Gurgevich, Elise
    'Horticulture': ['mcm2', ], # Masiuk, Michael
}

# Program Team Leaders
EPAS_TEAM_LEADERS = {

    '4-H Youth Development|Positive Youth Development' : [
        'jmb6036', # Stackhouse, Jeanette
        'dad7', # Dietrich, Deb
        'sab25', # Boarts, Suzanne
    ],

    '4-H Youth Development|Science' : [
        'pag2', # Anderson, Patty
        'kek170', # Dubbs, Kirsten
        'dfm6', # McFarland, Paul
    ],

    '4-H Youth Development|Volunteer Management and Development' : [
        'mjm20', # Martin, Michael
    ],

    'Agronomy and Natural Resources|Farm Safety' : [
        'lmf8', # Fetzer, Linda
    ],

    'Agronomy and Natural Resources|Field and Forage Crops' : [
        'nls18', # Nicole Santangelo/Thompson
    ],

    'Agronomy and Natural Resources|Forestry and Wildlife' : [
        'sjw128', # Weikert, Scott
    ],

    'Agronomy and Natural Resources|Master Watershed Steward' : [
        'elf145', # Frederick, Erin
    ],

    'Agronomy and Natural Resources|Pesticide Education' : [
        'jmj5', # Johnson, Jon
    ],

    'Agronomy and Natural Resources|Urban Forestry' : [
        'vjc1', # Vinnie Cotrone
    ],

    'Agronomy and Natural Resources|Water Quality and Quantity' : [
        'jrf21',  # Fetter, Jennifer
    ],

    'Animal Systems|Dairy' : [
        'clm275', # Yost, Cassie
    ],

    'Animal Systems|Equine' : [
        'dxs1172', # Smarsh, Danielle
    ],

    'Animal Systems|Farm Animal Welfare' : [
        'eph1', # Hovingh, Ernest
    ],

    'Animal Systems|Livestock' : [
        'meh7', # Barkley, Melanie
    ],

    'Animal Systems|Poultry' : [
        'jxb2002', # Boney, John
    ],

    'Energy, Business, and Community Vitality|Business, Entrepreneurship, and Economic Development' : [
        'cus24', # Snyder, Carla
    ],

    'Energy, Business, and Community Vitality|Energy' : [
        'dlb14', # Brockett, Daniel
    ],

    'Energy, Business, and Community Vitality|Leadership and Community Vitality' : [
        'dlb14', # Brockett, Daniel
    ],

    'Energy, Business, and Community Vitality|New and Beginning Farmer' : [
        'lfk4', # Kime, Lynn
        'cus24', # Snyder, Carla
    ],

    'Food Safety and Quality|FSMA' : [
        'lfl5', # LaBorde, Luke
    ],

    'Food Safety and Quality|Industrial Food Safety and Quality' : [
        'mwb124', # Bucknavage, Martin
    ],

    'Food Safety and Quality|Retail, Food Service, and Consumer Food Safety' : [
        'ajh284', # Hirneisen, Andy
    ],

    'Food, Families, and Health|Family Well-being' : [
        'jla17', # Amor-Zitzelberger, Jacque
        'cep5', # Pollich, Cynthia
    ],

    'Food, Families, and Health|Health and Wellness' : [
        'mxg37', # Gettings, Mary Alice
        'sls374', # Reed, Stacy
    ],

    'Food, Families, and Health|Vector Borne Diseases' : [
        'etm10', # Machtinger, Erika
    ],

    'Horticulture|Grape and Enology' : [
        'cch5027', # Hickey, Cain
        'mxk1171', # Kelly, Molly
    ],

    'Horticulture|Green Industry' : [
        'exs33', # Swackhamer, Emelie
        'tmb124', # Butzler, Tom
    ],

    'Horticulture|Master Gardener' : [
        'avf100', # Faust, Andy
    ],

    'Horticulture|Tree Fruit' : [
        'dew326', # Weber, Daniel
        'dus970', # Seifrit, Don
    ],

    'Horticulture|Vegetable, Small Fruit, Mushroom, and Pollinator' : [
        'rcp3', # Pollock, Robert
        'bmk120', # Gugino, Beth
    ],

}

UID_RE = re.compile("^([abcdef0-9]{32})$", re.I|re.M)
RESOLVEUID_RE = re.compile("resolveuid/([abcdef0-9]{32})", re.I|re.M)
