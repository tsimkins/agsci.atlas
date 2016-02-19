XML Export
==========

Append `/@@api` to the URL for a piece of content.

JSON
----
For JSON equivalent, use `/@@api/json` instead.

URL Parameters
--------------

 * **bin=(true|false)** - Default: true.  Setting to false omits the base64 encoded data for files and images.
 * **recursive=(true|false)** - Default: true.  Setting to false will only show the data for the object against which `@@api` is called, and not any child objects.

Lookup by UID
-------------

To pull data for a known object by its Plone Unique ID (e.g. '5945eeb87960461993f42bc6cfe80f0d') for content, the API can be called from the root of the site, as:

    http://[site URL]/@@api?uid=[UID]

XML Data Schema
===============

Content Type-Specific Documentation
-----------------------------------

 * [Article](article.md)
 * [Person](person.md)
 * [Event](event.md) 
 * [Video](video.md)
 
Item
----
`<item>` - An individual 'item' of data (e.g. piece of content, or an item in a list.)

All Items
---------
`<plone_id>` - Plone Unique ID for item

`<url_key>` - URL path for item in Plone

`<short_name>` - Last URL segment (slug) for item

`<name>` - Title of item

`<description>` - Short description of item

`<product_type>` - Type of item (e.g. Article, Article Page, Slideshow, File, Image, Link, etc.)

Products
--------

Items that are products, specifically:

 * Article
 * Person
 * Event
 
contain extra data about that item, specifically for Magento.

### Categories

`<category>` - First level category (e.g. "Animals and Livestock")

`<subcategory>` - Second level category (e.g. "Dairy")

`<category_level_3>` - Third level category (e.g. "Dairy Herd Management")

Each of these category of hierarchy is presented as a list of `<item>` values.

The value inside the `<item>` tag is an integer id of the corresponding Magento category.

### Product Metadata

`<home_or_commercial>` - Home or Commercial

`<language>` - Language (English, Spanish)

### People

`<authors>` - List of Penn State user ids that are authors/speakers/instructors for the product (list of `<item>` tags.)

`<primary_contact_psu_user_id>` - Primary contact for internal use, responsible for reviewing the article.

### Dates

`<publish_date>` - Publish date

`<updated_at>` - Last Updated date

`<product_expiration>` - Expiration date

### Magento Statuses

`<product_status>` - Magento Product Status

`<status>` - Magento Status

`<visibility>` - Magento Visibility

### Plone Status

`<plone_status>` - Plone workflow state (e.g., 'private', 'published')

Lead Image
---------------

Items can contain a lead image and image caption.

`<leadimage>` - Information on the Lead Image for the Article.

 * `<caption>` - Image Caption
 * `<mimetype>` - Mimetype (e.g. "image/jpeg", "image/png") for image
 * `<data>` - base64 encoded data


Body Text
---------

`<text>` - Body text (HTML) for item