
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

Metadata
-------------

Some items, specifically:

 * Article
 * Person
 
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
 * `<subtopic>`

Lead Image
---------------

Some items, specifically:

 * Article
 * Person
 
contain a lead image and image caption.

`<leadimage>` - Information on the Lead Image for the Article.

 * `<caption>` - Image Caption
 * `<mimetype>` - Mimetype (e.g. "image/jpeg", "image/png") for image
 * `<data>` - base64 encoded data

Person
------

`<username>` - Individual's Penn State username/login name (e.g. 'xyz123')

`<name>` - Structure containing information about the individual's name:

  * `<first>` - First name
  * `<middle>` - Middle name
  * `<last>` - Last name
  * `<suffix>` - Suffix (e.g. Jr., Ph.D., II, etc.)

`<contact>` - Contact information for the individual, containing:

  * `<email>` - Email address ('xyz123@psu.edu')
  * `<office_phone>` - Office phone number ('814-555-1212')
  * `<fax_number>` - Office fax number ('814-555-1212')
  * `<venue>` - Office building name
  * `<office_address>` - Street address
  * `<office_city>` - City
  * `<office_state>` - State
  * `<office_zip_code>` - ZIP code

`<professional>` - Professional information for the user, including:

  * `<areas_expertise>` - List of specific areas of expertise (user provided)
  * `<bio>` - Rich text field containing biographical information
  * `<classifications>` - Faculty, Staff, Educator, etc.
  * `<counties>` - Counties that the individual is affiliated with (if county-based)
  * `<education>` - List of degrees (e.g. 'Ph.D., The Pennsylvania State University, Generic Studies, 2001')
  * `<job_titles>` - List of job titles for individual

`<social_media>` - Links to individual's social media pages

 * `<facebook_url>` - Facebook
 * `<google_plus_url>` - Google Plus
 * `<linkedin_url>` - LinkedIn
 * `<twitter_url>` - Twitter

Additional notes:

 * The `<title>` for a person contains a system-generated full name
 * The `<leadimage>` data structure contains the individual's portrait

Article
-------
`<page_count>` - Number of "pages" (including Article Page, Slideshow, Video) inside article.

`<multi_page>` - Boolean True if page_count > 1, otherwise False.

`<dates>` - Dates for the article

 * `<created>` - Initial creation date
 * `<effective>` - Published date
 * `<expires>` - Expiration date
 * `<modified>` - Last modified date
    
`<people>` - People involved in the article, presented as Penn State ids as an `<item>`

 * `<creators>` - Individuals responsible for reviewing the article
 * `<contributors>` - Individuals responsible for the content of the article (e.g. authors)
    
`<workflow_state>` - Workflow state (states TBD) for item
    
`<related_items>` - `<item>` list, each with UID for related items. These may be inside or outside the Article object.
    
`<contents>` - List of objects contained within article (e.g. Article Page, Slideshow, File, Image, Link, etc.)


Article Page
------------
`<text>` - Body text for individual page


Slideshow
---------
`<text>` - Body text for slideshow

`<contents>` - List of "Image" objects


Video
---------
`<video_id>` - Unique id for video in external provider's system

`<video_provider>` - External video provider's name (e.g. 'youtube', 'vimeo'.)

`<video_aspect_ratio>` - Aspect ratio of source video (e.g. '16:9', '3:2', '4:3') 

`<video_aspect_ratio_decimal>` - Aspect ratio of source video in decimal format (e.g. 1.7778, 1.5, 1.3333)
 

File and Image
--------------
`<mimetype>` - Mimetype (e.g. "image/jpeg", "application/pdf") for file or image

`<data>` - base64 encoded data


Link
----
`<remote_url>` - URL of the link destination
