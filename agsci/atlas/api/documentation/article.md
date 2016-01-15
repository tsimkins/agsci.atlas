Article API Documentation
=========================

Article Structure
-----------------

An article can contain:

   * Article Page
   * Slideshow
   * Image
   * File
   * Link

Each of those is a "leaf" node, except the "Slideshow", which contains multiple "Image" objects.


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