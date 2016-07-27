# Publication API Documentation

## Publication fields

In addition to the standard product fields, **Publication** products also have these fields:

`<product_platform>` - This will be 'Salesforce', since publications originate in Salesforce.

`<pages_count>` - Number of pages in the publication

`<file>` - Sample file (usually PDF) of download. This tag contains:

 * `<mimetype>` - Mimetype (e.g. "application/pdf") for file
 * `<data>` - base64 encoded data

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?
