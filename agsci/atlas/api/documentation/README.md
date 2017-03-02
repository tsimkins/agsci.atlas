# Plone Integration API Documentation

## API Output Formats

### XML

Append `/@@api` to the URL for a piece of content.

### Example:

 * `http://[site_url]/path/to/product/@@api`


### JSON

For JSON equivalent, use `/@@api/json` instead.

#### Example

 * `http://[site_url]/path/to/product/@@api/json`

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

### Parameters for all API calls

 * **bin=(true|false)** - Default: **true**.  Setting to **false** omits the base64 encoded data for files and images.
 * **recursive=(true|false)** - Default: **true**.  Setting to **false** will only show the data for the object against which `@@api` is called, and not any child objects.
 
### Additional parameters for API calls against an individual object

These parameters determine the inclusion of [subproducts and shadow products](#subproducts-and-shadow-products) in the API output of an individual object.

 * **all=(true|false)** - Default: **false**.  Setting to **true** will show the API output as a list of products rather of a single product.  The purpose is to show any subproducts or shadow products for the object in addition to the output for that object.

 * **sku=[SKU]** - Default: **none**.  Passing the SKU into a product with subproducts or shadow products will present output for the single product with that SKU.  If the main product does not have a subproducts or shadow products with that SKU, an empty value will be returned.

### Examples

#### XML

 * `http://[site_url]/path/to/product/@@api?bin=false` - Return XML output, omitting binary data for files and images
 * `http://[site_url]/path/to/product/@@api?recursive=false` - Return XML output, omitting any child items (e.g. Article Pages, Images, etc.)
 * `http://[site_url]/path/to/product/@@api?bin=false&recursive=false` - Return XML output, omitting binary data for files and images, and any child items.

#### JSON

 * `http://[site_url]/path/to/product/@@api/json?bin=false` - Return JSON output, omitting binary data for files and images
 * `http://[site_url]/path/to/product/@@api/json?recursive=false` - Return JSON output, omitting any child items (e.g. Article Pages, Images, etc.)
 * `http://[site_url]/path/to/product/@@api/json?bin=false&recursive=false` - Return JSON output, omitting binary data for files and images, and any child items.

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

## Subproducts and Shadow Products

In some cases, one Plone product object may be used to represent multiple similar products in Salesforce and Magento.  This avoids having to manage separate objects in Plone where only a few fields may differ, and is presented (relatively) transparently through the API.

### Definitions

A **Subproduct** is a child of a group product with child products (analogus to a Magento configurable product.)  An example would be a Publication that has multiple formats (hardcopy, digital, and bundled.)  In this case, almost all of the information would be identical, except SKU, format, and price.

A **Shadow Product** is a single product that has a counterpart in a secondary, alternate format.  An example would be an Article which is web content, but can also be purchased as a hardcopy Publication.  Again, the nformation would be almost identical, except SKU and price.

### API output

Subproducts are shown under the `<contents>` tag of the main product in both the product feed (`http://[site URL]/@@api`) and the individual product API call (`http://[site_url]/path/to/product/@@api`).  In the Publication example, the main product would be the grouped product, and the `<contents>` tag would contain one product for each format in which the publication is offered.

In the product feed API call, subproducts and shadow products are presented in parallel with the main product.  The `<api_url_xml>` and `<api_url_json>` fields in those product representations use the `sku=[SKU]` parameter to point to the unique URL for that particular product.

In the individual product API call, only the main product is shown by default.  If the `all=true` URL parameter is used, all subproducts and shadow products for the main product will be shown in parallel.  If the `sku=[SKU]` URL parameter is used, only the subproduct or shadow product with that SKU will be shown.

#### Fields

`<is_sub_product>` - If an object is a subproduct or shadow product, its representation contains a this field with a value of **true**.

`<visibility>` - This field is set to "Not Visible Individually" for subproducts and shadow products.

## XML Data Schema

[Documentation for the specific fields used in the XML output](schema.md)

## API Output Samples

These are samples of the main product feed, containing one composite example product structure.
 
 * [XML](sample.xml)
 * [JSON](sample.json)