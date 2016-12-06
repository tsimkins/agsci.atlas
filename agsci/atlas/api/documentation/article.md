# Article API Documentation

## Article Structure

An article can contain:

   * Article Page
   * Slideshow
   * Image
   * File
   * Link

Each of those is a "leaf" node, except the "Slideshow", which contains multiple "Image" objects.


## Article

`<pages_count>` - Number of "pages" (including Article Page, Slideshow, Video) inside article.

`<multi_page>` - Boolean True if pages_count > 1, otherwise False.

`<publication_reference_number>` - SKU of print publication associated with this article.

`<contents>` - List of objects contained within article (e.g. Article Page, Slideshow, File, Image, Link, etc.)


## Article Page

`<description>` - Body text for individual page


## Slideshow

`<description>` - Body text for slideshow

`<contents>` - List of "Image" objects


## Video

This contains the fields listed in the "Basic Fields" heading as the standalone [Video](video.md) product.


## File and Image

`<mimetype>` - Mimetype (e.g. "image/jpeg", "application/pdf") for file or image

`<data>` - base64 encoded data


## Link

`<remote_url>` - URL of the link destination