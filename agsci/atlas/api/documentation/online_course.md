# Online Course API Documentation

## Online Course fields

In addition to the [standard product fields](schema.md#all-products), **Online Course** products also have these fields:

`<edx_id>` - Unique identifier for the course in edX

`<price>` - The price of the product, if it is for sale

`<length_content_access>` - Length of content access

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<skill_level>` - Skill Level (Beginner, Intermediate, Advanced)

`<credits>` - Credits/CEUs.  This format is the same as for the [Event Credits/CEUs](event.md#event-creditsceu).

`<sections>` - Online Course Sections (generally a number)

`<duration_formatted>` - Duration of the course in the format 'X hours, Y minutes'

`<oc_allow_bulk_registration>` - Allow bulk registration for online course.

## Registration Fields

`<event_start_date>` - Start date of synchronous online course.

`<event_end_date>` - End date of synchronous online course.

`<registration_deadline>` - Registration deadline for synchronous online course.

Online courses share these fields from the Workshop/Webinar types:

 * [Registration Form Fields](event.md#registration-form-fields)
 * [Ticket Type](event.md#ticket-type)

## Product Page Note

`<product_page_note>` - Short text to be featured in a callout on the product page.