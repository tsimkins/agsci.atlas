# County

This product type provides the data for the county Extension office.  In addition
to the standard [Contact Information](person.md#contact-information) and [Social Media](person.md#social-media) fields used for a person, a **County** also has:

`<county_4h_url>` - URL for county 4-H site

`<county_master_gardener_url>` - URL for county Master Gardener site

`<office_hours>` - List of `<item>` tags with office hours.  Multiple `<item>` tags may be used if there are different daily hours.

`<client_relations_manager>` - List of `<item>` tags containing the Penn State ids (e.g. 'xyz123') of the CRMs.

`<business_operations_manager>` - List of `<item>` tags containing the Penn State ids (e.g. 'xyz123') of the BOMs.

## Examples

Note that this is a simplified example that only contains the county-specific fields, and not the standard product or other API fields.

### XML

    <item>
        <county_4h_url>//[site]/programs/4-h/counties/centre</county_4h_url>
        <fax>814-355-6983</fax>
        <short_name>centre</short_name>
        <name>Centre County</name>
        <venue>Willowbank Building</venue>
        <linkedin_url>http://linkedin.com/USER</linkedin_url>
        <plone_product_type>County</plone_product_type>
        <email_address>CentreExt@psu.edu</email_address>
        <state>PA</state>
        <address>
            <item>420 Holmes Street</item>
            <item>Willowbank Building, Room 322</item>
        </address>
        <county>Centre</county>
        <google_plus_url>http://google.com/USER</google_plus_url>
        <city>Bellefonte</city>
        <state>PA</state>
        <zip>16823-1488</zip>
        <latitude>40.90653499</latitude>
        <longitude>-77.78310700</longitude>
        <visibility>Catalog, Search</visibility>
        <phone>814-355-4897</phone>
        <office_hours>
            <item>Monday-Friday 8:30 a.m. - 5:00 p.m.</item>
        </office_hours>
        <county_master_gardener_url>//[site]/programs/master-gardener/counties/centre</county_master_gardener_url>
        <county_other_url>//[site]/extension-directory/centre-county</county_other_url>
        <twitter_url>http://twitter.com/USER</twitter_url>
        <facebook_url>http://facebook.com/USER</facebook_url>
        <map_link>http://maps.google.com/path</map_link>
        <product_type>County</product_type>
        <business_operations_manager>
            <item>xyz123</item>
        </business_operations_manager>
        <client_relations_manager>
            <item>xyz123</item>
        </client_relations_manager>
    </item>

### JSON

    {
        "address": [
            "420 Holmes Street",
            "Willowbank Building, Room 322"
        ],
        "city": "Bellefonte",
        "county": "Centre",
        "county_4h_url": "//[site]/programs/4-h/counties/centre",
        "county_master_gardener_url": "//[site]/programs/master-gardener/counties/centre",
        "county_other_url" : "//[site]/extension-directory/centre-county",
        "email_address": "CentreExt@psu.edu",
        "facebook_url": "http://facebook.com/USER",
        "fax": "814-355-6983",
        "latitude": "40.90653499",
        "longitude": "-77.78310700",
        "google_plus_url": "http://google.com/USER",
        "linkedin_url": "http://linkedin.com/USER",
        "map_link": "http://maps.google.com/path",
        "name": "Centre County",
        "office_hours": [
            "Monday-Friday 8:30 a.m. - 5:00 p.m."
        ],
        "phone": "814-355-4897",
        "plone_product_type": "County",
        "product_type": "County",
        "short_name": "centre",
        "state": "PA",
        "twitter_url": "http://twitter.com/USER",
        "venue": "Willowbank Building",
        "zip": "16823-1488",
        "business_operations_manager" : [
            'xyz123',
        ],
        "client_relations_manager" : [
            'xyz123',
        ]
    }