# Publication API Documentation

## Publication fields

In addition to the [standard product fields](schema.md#all-products), **Publication** products also have these fields:

`<product_platform>` - This will be 'Salesforce', since publications originate in Salesforce.

`<pages_count>` - Number of pages in the publication

`<pdf_sample>` - Sample PDF file of download. This tag contains:

 * `<mimetype>` - Mimetype (e.g. "application/pdf") for file
 * `<data>` - base64 encoded data

`<pdf>` - Full PDF file of download. This tag contains:

 * `<mimetype>` - Mimetype (e.g. "application/pdf") for file
 * `<data>` - base64 encoded data

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<bundle_publication_sku>` - Indicates the SKU for a bundled (e.g. both hardcopy and digital) publication.

`<price>` - The price of the product, if it is for sale.  If this is a group product that has a `<bundle_publication_sku>`, this indicates the price of the bundle.

## Product Page Note

`<product_page_note>` - Short text to be featured in a callout on the product page.