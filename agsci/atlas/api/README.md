
Article Structure
=================

An article can contain:

   * Article Page
   * Slideshow
   * Image
   * File
   * Link

Each of those is a "leaf" node, except the "Slideshow", which contains multiple "Image" objects.

XML Export
==========

Append `/@@api` to a piece of content.

JSON
----
For JSON equivalent, use `/@@api/json` instead.

XML Data Schema
===============

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

Article
-------
`<page_count>` - Number of "pages" (including Article Page, Slideshow, Video) inside article.

`<multi_page>` - Boolean True if page_count > 1, otherwise False.

`<leadimage>` - Information on the Lead Image for the Article.

 * `<caption>` - Image Caption
 * `<mimetype>` - Mimetype (e.g. "image/jpeg", "image/png") for image
 * `<data>` - base64 encoded data
    
`<dates>` - Dates for the article

 * `<created>` - Initial creation date
 * `<effective>` - Published date
 * `<expires>` - Expiration date
 * `<modified>` - Last modified date
    
`<people>` - People involved in the article, presented as Penn State ids

 * `<creators>` - Individuals responsible for reviewing the article
 * `<contributors>` - Individuals responsible for the content of the article (e.g. authors)
    
`<workflow_state>` - Workflow state (states TBD) for item
    
`<metadata>` - Hierarchical categorization for Article

 * `<category>`
 * `<program>`
 * `<topic>`
 * `<subtopic>`
    
`<related_items>` - `<item>` list, each with UID for related items. These may be inside or outside the Article object.
    
`<contents>` - List of objects contained within article (e.g. Article Page, Slideshow, File, Image, Link, etc.)


Article Page
------------
`<text>` - Body text for individual page


Slideshow
---------
`<text>` - Body text for slideshow

`<contents>` - List of "Image" objects


File and Image
--------------
`<mimetype>` - Mimetype (e.g. "image/jpeg", "application/pdf") for file or image

`<data>` - base64 encoded data


Link
----
`<remote_url>` - URL of the link destination
