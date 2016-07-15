# News Item API Documentation


## News Item Structure

A News Item is very similar to an Article, but all of the text content is contained within the `<description>` tag, rather than being spread across multiple pages.

An news item can contain:

   * Slideshow
   * Video
   * Image
   * File

Each of those is a "leaf" node, except the "Slideshow", which contains multiple "Image" objects.

More information on the API output for the types above can be found in the [Article](article.md) documentation.


## News Item

`<county>` - County or counties referenced by News Item. These are listed as `<item>` tags inside the `<county>` tag.

`<page_count>` - Number of "pages" (specifically a Slideshow) inside news item.

`<multi_page>` - Boolean True if page_count > 1, otherwise False.

`<contents>` - List of objects contained within article (e.g. Slideshow, File, Image, etc.)