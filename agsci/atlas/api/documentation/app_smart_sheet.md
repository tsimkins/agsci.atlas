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

## App Available Formats

This lists the available formats (app store names) and links to the download page.

Current values for the `<title>` attribute are:

  * Apple iOS
  * Google Play
  * Web-based Application

### Examples

#### XML

    <available_formats>
        <item>
            <title>Apple iOS</title>
            <url>https://www.apple.com/...</url>
        </item>
        <item>
            <title>Google Play</title>
            <url>https://play.google.com/...</url>
        </item>
    </available_formats>

#### JSON

    "available_formats": [
        {
            "title": "Apple iOS",
            "url": "https://www.apple.com/..."
        },
        {
            "title": "Google Play",
            "url": "https://play.google.com/..."
        }
    ],

## Product Page Note

`<product_page_note>` - Short text to be featured in a callout on the product page.