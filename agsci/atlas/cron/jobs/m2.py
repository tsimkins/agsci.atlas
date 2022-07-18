from Products.CMFPlone.utils import safe_unicode

from .magento import SetMagentoInfo as _SetMagentoInfo

from agsci.atlas.constants import M2_DATA_URL

class SetMagentoInfo(_SetMagentoInfo):

    title = "Set Magento SKU/URL (M2)"

    cache_key = 'M2_DATA'
    MAGENTO_DATA_URL = M2_DATA_URL

    # Hard Code enabled
    enabled = True

    @property
    def updates(self):

        # Get all products from Magento
        results = self.portal_catalog.searchResults({
            'UID' : self.plone_ids,
            'object_provides' : 'agsci.atlas.content.behaviors.IAtlasInternalMetadata',
        })

        for r in results:

            _ = self.by_plone_id(r.UID)

            if not _:
                continue

            # Holds attributes to be updated
            _updates = {}

            # Plone Product Values
            sku = r.SKU
            magento_url = r.MagentoURL

            # Magento Product Values
            _sku = _.get('sku')
            _magento_url = _.get('magento_url')

            # If Plone doesn't match Magento
            if _magento_url != magento_url or _sku != sku:

                if _magento_url and magento_url != _magento_url:

                    self.log(u"Set Magento URL to %s for %s %s" % (
                        _magento_url,
                        safe_unicode(r.Type),
                        safe_unicode(r.Title))
                    )

                    _updates['magento_url'] = _magento_url

                if _sku and sku != _sku:

                    self.log(u"Set SKU to %s for %s %s" % (
                        _sku,
                        safe_unicode(r.Type),
                        safe_unicode(r.Title))
                    )

                    _updates['sku'] = _sku

                # If the object was modified, return that data.
                if _updates:
                    yield (r, _updates)