# XML Data Schema

The information in this section describes the schema elements that are common to all products.

## Product-specific Information

Items that are defined as products for the purposes of Salesforce and Magento, specifically:

 * [Article](article.md)
 * [Curriculum](curriculum.md)
 * [News Item](news_item.md)
 * [Online Course](online_course.md)
 * [Person](person.md)
 * [Publication](publication.md)
 * [App and Smart Sheet](app_smart_sheet.md)
 * [Video](video.md)
 * [Workshops, Webinars, and Conferences](event.md)

contain additional data specific to that type of item.

## All Products

### Basic Information

With the exception of `<product_platform>`, this basic information also applies to the items contained within a product (e.g. an Article Page inside an Article.)

`<plone_id>` - Plone Unique ID for item. This *is* a globally unique value.

`<external_url>` - URL path for item in Plone

`<api_url_xml>` - URL path for the XML representation of the product. This will always be `<external_url>/@@api`

`<api_url_json>` - URL path for the XML representation of the product. This will always be `<external_url>/@@api/json`

`<product_type>` - Type of item (e.g. Article, Article Page, Slideshow, File, Image, Link, etc.)

`<product_platform>` - Source platform (system) for product.  Defaults to Plone, but can also be Cvent.

`<short_name>` - Last URL segment (slug) for item. This *is not* a globally unique value.

`<name>` - Name of item

`<short_description>` - Short description of item

`<description>` - Body text (HTML) for item

`<sku>` - SKU of product. Note that this is assigned by Salesforce, and later updated in Plone.

`<website_ids>` - List of `<item>` tags with possible values of "2" (External) or "3" (Internal).  One or both may be selected.

### Categories

The three levels of categories (Category Level 1, Category Level 2, and Category Level 3) used in the Magento information architecture are represented as a nested XML structure under the `<categories>` tag.

The "deepest" level of categorization implies all "shallower" levels.  In general, at least two, and usually three levels will be provided.

#### Examples

##### XML

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

##### JSON

    "categories": [
        [
            "Animals and Livestock",
            "Dairy",
            "Reproduction and Genetics"
        ],
        [
            "Animals and Livestock",
            "Beef Cattle",
            "Reproduction and Genetics"
        ]
    ],


### Extension Structure

This captures the Extension Program Activity System (EPAS) metadata for each product.


#### Examples

Each `<item>` tag directly under the `<extension_structure>` tag contains a set consisting of:

  * State Extension Team
  * Program Team
  * Curriculum

##### XML

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

##### JSON

    "extension_structure": [
        {
            "curriculum": "[Curriculum 1]",
            "program_team": "[Program Team 1]",
            "state_extension_team": "[State Extension Team 1]"
        },
        {
            "curriculum": "[Curriculum 2]",
            "program_team": "[Program Team 2]",
            "state_extension_team": "[State Extension Team 2]"
        }
    ],

### Product Attributes

Each of these tags may contain one or more`<item>` tags specifying the values selected out of that attribute set.

`<language>` - Language (English, Spanish)

`<home_or_commercial>` - Values from **Application** attribute set (e.g. 'Home', 'Commercial', or 'Classroom')

`<agronomic_crop>` - Values from **Agronomic Crop** attribute set

`<business_topic>` - Values from **Business Topic** attribute set

`<cover_crop>` - Values from **Cover Crop** attribute set

`<disaster>` - Values from **Disaster** attribute set

`<energy_source>` - Values from **Energy Source** attribute set

`<farm_structure>` - Values from **Farm Equipment/Structure** attribute set

`<forage_crop>` - Values from **Forage Crop** attribute set

`<fruit>` - Values from **Fruit** attribute set

`<industry>` - Values from **Industry** attribute set

`<plant_type>` - Values from **Plant Type** attribute set

`<turfgrass>` - Values from **Turfgrass/Lawn** attribute set

`<vegetable>` - Values from **Vegetable** attribute set

`<water_source>` - Values from **Water Source** attribute set


### People

`<authors>` - List of Penn State user ids that are authors/speakers/instructors for the product (list of `<item>` tags.)

`<owners>` - Individuals who are responsible for the content, not necessarily the authors. This is used internally, and not used by Magento.  It is presented as a list of `<item>` tags.

`<external_authors>` - Individuals that are authors/speakers/instructors, but are not part of Penn State Extension. There may be multiple individuals, and each individual is listed in following format:

#### XML

    <external_authors>
        <item>
            <name>[Person Name]</name>
            <job_title>[Person Job Title]</job_title>
            <organization>[Person Organization]</organization>
            <email>[Person Email Address]</email>
            <website>[Person Website URL]</website>
        </item>
        <item>
            ...
        </item>
    </external_authors>

#### JSON

    "external_authors": [
        {
            "name": "[Person Name]",
            "job_title": "[Person Job Title]",
            "organization": "[Person Organization]",
            "email": "[Person Email Address]",
            "website": "[Person Website URL]"
        }
        {
            ...
        }
    ],

`<primary_contact_psu_user_id>` - Primary contact for internal use, responsible for reviewing the article. This is the first id listed in the `<owners>` field.


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

`<plone_status>` - Plone workflow state (e.g., 'published', 'expired')


### Lead Image

Items can contain a lead image and image caption.

`<leadimage>` - Information on the Lead Image for the Article.

 * `<caption>` - Image Caption
 * `<mimetype>` - Mimetype (e.g. "image/jpeg", "image/png") for image
 * `<data>` - base64 encoded data

#### Examples

##### XML

    <leadimage>
        <mimetype>image/jpeg</mimetype>
        <caption>[Image caption]</caption>
        <data>[Binary image data]</data>
    </leadimage>

##### JSON

    "leadimage": {
        "caption": "[Image caption]",
        "mimetype" : "image/jpeg",
        "data" : "[Binary image data]"
    }
