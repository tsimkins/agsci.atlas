# XML Export

Append `/@@api` to the URL for a piece of content.


## JSON

For JSON equivalent, use `/@@api/json` instead.


## URL Parameters

 * **bin=(true|false)** - Default: true.  Setting to false omits the base64 encoded data for files and images.
 * **recursive=(true|false)** - Default: true.  Setting to false will only show the data for the object against which `@@api` is called, and not any child objects.


## Lookup by UID

To pull data for a known object by its Plone Unique ID (e.g. '5945eeb87960461993f42bc6cfe80f0d') for content, the API can be called from the root of the site, as:

    http://[site URL]/@@api?uid=[UID]


## Lookup by Last Updated Time

To pull data for all products that were last updated within a certain timeframe, the API can be called from the root of the site with an `updated` parameter, e.g.:

    http://[site URL]/@@api?updated=[seconds]

This will show all products that were last updated less than that number of seconds ago.  This (intentionally) does not include **Person** objects.


# XML Data Schema


## Content Type-Specific Documentation

 * [Article](article.md)
 * [News Item](news_item.md)
 * [Person](person.md)
 * [Workshops and Webinars](event.md)
 * [Video](video.md)


## Item

`<item>` - An individual 'item' of data (e.g. piece of content, or an item in a list.)


## All Items

`<plone_id>` - Plone Unique ID for item

`<external_url>` - URL path for item in Plone

`<short_name>` - Last URL segment (slug) for item. This is not a unique value.

`<name>` - Title of item

`<short_description>` - Short description of item

`<product_type>` - Type of item (e.g. Article, Article Page, Slideshow, File, Image, Link, etc.)


## Products

Items that are products, specifically:

 * Article
 * Person
 * Workshop
 * Webinar

contain extra data about that item, specifically for Magento.


### Categories

The three levels of categories (Category Level 1, Category Level 2, and Category Level 3) used in the Magento information architecture are represented as a nested XML structure under the `<categories>` tag.


#### Example

    <categories>
        <item>
            <item>Animals and Livestock</item>
            <item>Dairy</item>
            <item>Reproduction and Genetics</item>
        </item>
        <item>
            <item>Animals and Livestock</item>
            <item>Beef Cattle</item>
            <item>Reproduction and Genetics</item>
        </item>
    </categories>

Each `<item>` tag directly under the `<categories>` tag contains up to three levels of categorization, which are themselves listed as `<item>` tags.

The "deepest" level of categorization implies all "shallower" levels.  In general, at least two, and usually three levels will be provided.


### Extension Structure

This captures the Extension Program Activity System (EPAS) metadata for each product.


#### Example

    <extension_structure>
        <item>
            <state_extension_team>[State Extension Team 1]</state_extension_team>
            <program_team>[Program Team 1]</program_team>
            <curriculum>[Curriculum 1]</curriculum>
        </item>
        <item>
            <state_extension_team>[State Extension Team 2]</state_extension_team>
            <program_team>[Program Team 2]</program_team>
            <curriculum>[Curriculum 2]</curriculum>
        </item>
    </extension_structure>

Each `<item>` tag directly under the `<extension_structure>` tag contains a set consisting of:

  * State Extension Team
  * Program Team
  * Curriculum


### Product Metadata

`<language>` - Language (English, Spanish)

`<home_or_commercial>` - Home or Commercial audience.  One or both options may be selected.


### People

`<authors>` - List of Penn State user ids that are authors/speakers/instructors for the product (list of `<item>` tags.)

`<owners>` - Individuals who are responsible for the content, not necessarily the authors. This is used internally, and not used by Magento.

`<primary_contact_psu_user_id>` - Primary contact for internal use, responsible for reviewing the article.


### Dates

`<publish_date>` - Publish date

`<updated_at>` - Last Updated date

`<product_expiration>` - Expiration date


### Magento Visibility

`<visibility>` - Magento visibility setting

Options:

 * Catalog, Search
 * Not Visible Individually


### Plone Status

`<plone_status>` - Plone workflow state (e.g., 'private', 'published')


## Lead Image

Items can contain a lead image and image caption.

`<leadimage>` - Information on the Lead Image for the Article.

 * `<caption>` - Image Caption
 * `<mimetype>` - Mimetype (e.g. "image/jpeg", "image/png") for image
 * `<data>` - base64 encoded data


## Body Text

`<description>` - Body text (HTML) for item