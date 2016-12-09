# App and Smart Sheet API Documentation

## App and Smart Sheet Fields

In addition to the [standard product fields](schema.md#all-products), **App** and **Smart Sheet** products also have these fields:

`<price>` - The price of the product, if it is for sale

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<skill_level>` - Skill Level (Beginner, Intermediate, Advanced)

## App and Smart Sheet Structure

The App and Smart Sheet product type may contain:

  * File
  * Image

that can be referenced in the `<description>` field HTML.

## Product Page Note

`<product_page_note>` - Short text to be featured in a callout on the product page.