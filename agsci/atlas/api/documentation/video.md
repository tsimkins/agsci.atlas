# Video API Documentation

## Basic Video Fields

`<video_url>` - URL of the video in the external provider's system

`<video_id>` - Unique id for video in external provider's system

`<video_provider>` - External video provider's name (e.g. 'youtube', 'vimeo'.)

`<video_aspect_ratio>` - Aspect ratio of source video (e.g. '16:9', '3:2', '4:3')

`<video_aspect_ratio_decimal>` - Aspect ratio of source video in decimal format (e.g. 1.7778, 1.5, 1.3333)

`<video_channel_id>` - Video channel id in provider system.


## Learn Now Video Product Fields

`<transcript>` - Video transcript (plain text)

`<video_duration_milliseconds>` - Video duration in ms (integer)

`<duration_formatted>` - Video duration (formatted)


## Product Page Note

`<product_page_note>` - Short text to be featured in a callout on the product page.

## Learn Now Video Series

The `<contents>` field in a Video Series product provides the listing of Learn Now Video products (each inside an `<item>`) that are part of the series in the order they should be listed.  The `<videos>` field is a synonym for `<contents>`.

The `<sku>` attribute contains the SKU of the video, and an optional `<name>` attribute that should override the name of the video product for only this listing.  The actual title of the video may not be appropriate for the series (e.g. it may contain the name of the series, or "Part 1 of 4".)

### Example: XML

    <contents>
        <item>
            <sku>VID-1234</sku>
            <name>Another title</name>
        </item>
        <item>
            <sku>VID-4567</sku>
            <name />
        </item>
    </contents>

### Example: JSON

    "contents": [
        {
            "name": "Another title",
            "sku": "VID-1234"
        },
        {
            "name": null,
            "sku": "VID-4567"
        }
    ],