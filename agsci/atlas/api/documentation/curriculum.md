# Curriculum API Documentation

## Curriculum fields

In addition to the [standard product fields](schema.md#all-products), **Curriculum** products also have these fields:

`<pdf_sample>` - Sample PDF file of download. This tag contains:

 * `<mimetype>` - Mimetype (e.g. "application/pdf") for file
 * `<data>` - base64 encoded data

`<pdf>` - Full PDF file of download. This tag contains:

 * `<mimetype>` - Mimetype (e.g. "application/pdf") for file
 * `<data>` - base64 encoded data

`<price>` - The price of the product, if it is for sale

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<skill_level>` - Skill Level (Beginner, Intermediate, Advanced)

## Product Page Note

`<product_page_note>` - Short text to be featured in a callout on the product page.