XML Export
==========

Append `/@@api` to a piece of content.

JSON
----
For JSON equivalent, use `/@@api/json` instead.

XML Data Schema
===============


Content Type-Specific Documentation
-----------------------------------

 * [Article](article.md)
 * [Person](person.md)
 * [Event](event.md) 

Item
----
`<item>` - An individual 'item' of data (e.g. piece of content, or an item in a list.)

All Items
---------
`<uid>` - Unique ID for item

`<url>` - URL path for item

`<short_name>` - Last URL segment (slug) for item

`<title>` - Title of item

`<description>` - Short description of item

`<type>` - Type of item (e.g. Article, Article Page, Slideshow, File, Image, Link, etc.)

Metadata
-------------

Some items, specifically:

 * Article
 * Person
 * Event
 
contain metadata that describes their place in the information hierarchy of the site.

That tag is:

`<metadata>` - Categorization for Article using four levels of hierarchy. This is split into `<magento>` and `<plone>` sections, which have the same values, but system-specific terminology.  

Each of these levels of hierarchy (e.g. `<category_level_1>` being a level) is presented as a list of `<item>` values.

The value inside the `<item>` tag is a colon-delimited hierarchy of individual level values up to that level. 

For example, a value for an `<item>` tag within `<category_level_3>` would be of the form:

`category_level_1:category_level_2:category_level_3`

e.g. `Animals:Dairy:Dairy Herd Management`.

`<magento>` section:

 * `<category_level_1>`
 * `<category_level_2>`
 * `<category_level_3>`
 * `<filters>`

`<plone>` metadata:

 * `<category>`
 * `<program>`
 * `<topic>`
 * `<filters>`

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