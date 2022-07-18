from Products.CMFPlone.utils import safe_unicode

from .magento import SetMagentoInfo as _SetMagentoInfo

from agsci.atlas.constants import M2_DATA_URL

class SetMagentoInfo(_SetMagentoInfo):

    title = "Set Magento SKU/URL (M2)"

    cache_key = 'M2_DATA'
    MAGENTO_DATA_URL = M2_DATA_URL

    # Hard Code enabled
    enabled = True