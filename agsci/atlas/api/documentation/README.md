# Plone Integration API Documentation

## API Output Formats

### XML

Append `/@@api` to the URL for a piece of content.

### Example:

 * `http://[site_url]/path/to/content/@@api`


### JSON

For JSON equivalent, use `/@@api/json` instead.

#### Example

 * `http://[site_url]/path/to/content/@@api/json`

For consistency, this documentation references the XML format of the API output only. However, the JSON format uses the same key names as the XML tags.

The major difference is that the XML format uses the `<item>` tags to encapsulate data items, while the JSON format uses the standard JavaScript Object Notation format.

So, the XML output of:

    <item>
        <colors>
            <item>Red</item>
            <item>Green</item>
            <item>Blue</item>
        </colors>
    </item>

would be equivalent to the JSON output of:

    {
        "colors": [
            "Red",
            "Green",
            "Blue",
        ],
    }

## URL Parameters

 * **bin=(true|false)** - Default: true.  Setting to false omits the base64 encoded data for files and images.
 * **recursive=(true|false)** - Default: true.  Setting to false will only show the data for the object against which `@@api` is called, and not any child objects.

### Examples

#### XML

 * `http://[site_url]/path/to/content/@@api?bin=false` - Return XML output, omitting binary data for files and images
 * `http://[site_url]/path/to/content/@@api?recursive=false` - Return XML output, omitting any child items (e.g. Article Pages, Images, etc.)
 * `http://[site_url]/path/to/content/@@api?bin=false&recursive=false` - Return XML output, omitting binary data for files and images, and any child items.

#### JSON

 * `http://[site_url]/path/to/content/@@api/json?bin=false` - Return JSON output, omitting binary data for files and images
 * `http://[site_url]/path/to/content/@@api/json?recursive=false` - Return JSON output, omitting any child items (e.g. Article Pages, Images, etc.)
 * `http://[site_url]/path/to/content/@@api/json?bin=false&recursive=false` - Return JSON output, omitting binary data for files and images, and any child items.


## Lookup by Plone Id (`plone_id`)

To pull data for a known object by its `plone_id` (e.g. '5945eeb87960461993f42bc6cfe80f0d'), the API can be called from the root of the site, as:

    http://[site URL]/@@api?uid=[plone_id]


## Lookup by Last Updated Time

### All Products excluding Person objects

To pull data for all products that were last updated within a certain timeframe, the API can be called from the root of the site with an `updated` parameter, e.g.:

    http://[site URL]/@@api?updated=[seconds]

This will show all products that were last updated less than that number of seconds ago.  This includes **Person** and **County** objects.

### All Person objects

To pull data for all Person objects that were last updated within a certain timeframe, the API can be called from the **directory** with an `updated` parameter, e.g.:

    http://[site URL]/directory/@@api?updated=[seconds]

This will show all Person objects that were last updated less than that number of seconds ago.

## Lookup by Last Updated Time Range

To query content last updated within a range of times, you can provide parameters of:

 * `updated_min` - Beginning of the range
 * `updated_max` - End of the range

The value for that parameter should be in the ISO-8601 format:

    YYYY-MM-DDTHH:MM:SS

For example:

    2016-07-01T00:00:00

### Example

These examples describe how to query content updated between 7/1/2016 and 7/31/2016.

#### All Products excluding Person objects

    http://[site URL]/@@api?updated_min=2016-07-01T00:00:00&updated_max=2016-07-31T23:59:59

#### All Person objects

    http://[site URL]/directory/@@api?updated_min=2016-07-01T00:00:00&updated_max=2016-07-31T23:59:59

## XML Data Schema

[Documentation for the specific fields used in the XML output](schema.md)