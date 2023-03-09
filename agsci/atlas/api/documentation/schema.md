# XML Data Schema

The information in this section describes the schema elements that are common to all products.

## Product-specific Information

Items that are defined as products for the purposes of Salesforce and Magento, specifically:

 * [Article](article.md)
 * [Curriculum](curriculum.md)
 * [County](county.md)
 * [News Item](news_item.md)
 * [Online Course](online_course.md)
 * [Person](person.md)
 * [Program](program.md)
 * [Publication](publication.md)
 * [App and Smart Sheet](app_smart_sheet.md)
 * [Video](video.md)
 * [Workshops, Webinars, and Conferences](event.md)

contain additional data specific to that type of item.

## All Products

### API URLs

`<api_url_xml>` - URL path for the XML representation of the product. This will always be `http://[site]/path/to/content/@@api`

`<api_url_json>` - URL path for the XML representation of the product. This will always be `http://[site]/path/to/content/@@api/json`

If the URL is for a subproduct or shadow product, it will contain a `?sku=[SKU]` parameter.

### Basic Information

With the exception of `<product_platform>`, this basic information also applies to the items contained within a product (e.g. an Article Page inside an Article.)

`<product_type>` - Normalized "object type" used by integration.

`<plone_product_type>` - Actual Plone "Type" of item (e.g. Article, Article Page, Slideshow, File, Image, Link, etc.)

`<attribute_set>` - Magento attribute set (calculated from `plone_product_type`)

`<education_format>` - Value for Magento front-end filter.

`<product_platform>` - Source platform (system) for product.  Defaults to Plone, but can also be Cvent or Salesforce.

`<short_name>` - Last URL segment (slug) for item. This *is not* a globally unique value.

`<name>` - Name of item

`<short_description>` - Short description of item

`<description>` - Body text (HTML) for item

`<sku>` - SKU of product. Note that this is assigned by Salesforce, and later updated in Plone.

`<website_ids>` - List of `<item>` tags with possible values of "2" (External) or "3" (Internal).  One or both may be selected.

`<magento_url>` - URL of the product page in Magento

`<magento_image_url>` - URL of the product image in Magento

`<related_skus>` - List of `<item>` tags containing calculated skus that are related to this product.

`<alternate_language>` - List of `<item>` tags, each containing a `<language>` and `<sku>` child that defines equivalent products in other languages.

#### Examples for `<alternate_language>`

##### XML

    <alternate_language>
        <item>
            <sku>ART-1234</sku>
            <language>Spanish</language>
        </item>
        <item>
            <sku>ART-5679</sku>
            <language>French</language>
        </item>
    </alternate_language>

##### JSON

    "alternate_language": [
        {
            "language": "Spanish",
            "sku": "ART-1234"
        },
        {
            "language": "French",
            "sku": "ART-5679"
        }
    ],

### Categories

The three levels of categories (Category Level 1, Category Level 2, and Category Level 3) used in the Magento information architecture are represented as a nested XML structure under the `<categories>` tag.

The "deepest" level of categorization implies all "shallower" levels.  In general, at least two, and usually three levels will be provided.

#### Examples

##### XML

    <categories>
        <item>
            <item>Penn State Extension</item>
            <item>Animals and Livestock</item>
            <item>Dairy</item>
            <item>Reproduction and Genetics</item>
        </item>
        <item>
            <item>Penn State Extension</item>
            <item>Animals and Livestock</item>
            <item>Beef Cattle</item>
            <item>Reproduction and Genetics</item>
        </item>
    </categories>

Each `<item>` tag directly under the `<categories>` tag contains up to three levels of categorization, which are themselves listed as `<item>` tags.

##### JSON

    "categories": [
        [
            "Penn State Extension",
            "Animals and Livestock",
            "Dairy",
            "Reproduction and Genetics"
        ],
        [
            "Penn State Extension",
            "Animals and Livestock",
            "Beef Cattle",
            "Reproduction and Genetics"
        ]
    ],

### Primary Category

The `<primary_category>` tag defines the "primary" category for purposes of determining where the product lives in the site. This is presented in the same format as the `<categories>` tag.

#### Examples

##### XML

    <primary_category>
        <item>Penn State Extension</item>
        <item>Food Safety and Quality</item>
        <item>Food Service and Retail</item>
        <item>Food Service Safety</item>
    </primary_category>

##### JSON

    "primary_category": [
        "Penn State Extension", 
        "Food Safety and Quality", 
        "Food Service and Retail", 
        "Food Service Safety"
    ], 

### Category Positions

The `<category_positions>` tag defines a manual ordering for this product within the specific Level 3 categories to which it's assigned, *if* that's been manually configured.

In Plone, these are configured by SKU and position on the Category Level 3 objects, but they're provided in the API output of each product.

#### Examples

##### XML

    <category_positions>
        <item>
            <category>
                <item>Penn State Extension</item>
                <item>Animals and Livestock</item>
                <item>Dairy</item>
                <item>Business Management</item>
            </category>
            <position>2</position>
        </item>
        <item>
            <category>
                <item>Penn State Extension</item>
                <item>Animals and Livestock</item>
                <item>Dairy</item>
                <item>Reproduction and Genetics</item>
            </category>
            <position>7</position>
        </item>
    </category_positions>

Each `<item>` tag directly under the `<category_positions>` tag contains a `<category>` with up to three levels of categorization, which are themselves listed as `<item>` tags.  The `<position>` tag defines the integer position for the item within the category.

##### JSON

    "category_positions": [
        {
            "category": [
                "Penn State Extension",
                "Animals and Livestock",
                "Dairy",
                "Business Management"
            ],
            "position": 2
        },
        {
            "category": [
                "Penn State Extension",
                "Animals and Livestock",
                "Dairy",
                "Reproduction and Genetics"
            ],
            "position": 7
        }
    ],

### EPAS

This captures the Extension Program Activity System (EPAS) metadata for each product using the updated EPAS structure as of 11/2017.

#### Examples

Each `<item>` tag directly under the `<epas>` tag contains a set consisting of:

  * Team
  * Topic
  * Subtopic (may not exist for all Topics)

##### XML

    <epas>
        <item>
            <team>...</team>
            <topic>...</topic>
            <subtopic>...</subtopic>
        </item>
        <item>
            <team>...</team>
            <topic>...</topic>
            <subtopic>...</subtopic>
        </item>
    </epas>

##### JSON

    "epas": [
        {
            "team": "...",
            "topic": "...",
            "subtopic": "..."
        },
        {
            "team": "...",
            "topic": "...",
            "subtopic": "..."
        }
    ],

### EPAS (New)

#### Unit/Team/Topic

This captures the updated Extension Program Activity System (EPAS) metadata for each product.

Each `<item>` tag directly under the `<epas>` tag contains a set consisting of:

  * Unit
  * Program Team
  * Topic

#### Primary Team

The `<epas_primary_team>` tag contains a `<unit>` and `<team>` tag describing the primary Team for the product for reporting purposes.

#### Examples

##### XML

    <epas>
        <item>
            <unit>...</unit>
            <team>...</team>
            <topic>...</topic>
        </item>
        <item>
            <unit>...</unit>
            <team>...</team>
            <topic>...</topic>
        </item>
    </epas>
    <epas_primary_team>
        <unit>...</unit>
        <team>...</team>
    </epas_primary_team>

##### JSON

    "epas": [
        {
            "unit": "...",
            "team": "...",
            "topic": "..."
        },
        {
            "unit": "...",
            "team": "...",
            "topic": "..."
        },
    ],
    "epas_primary_team": {
        "team": "...",
        "unit": "..."
    },

### Extension Structure (Legacy)

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

Each of these tags may contain one or more `<item>` tags specifying the values selected out of that attribute set.

`<language>` - Language (English, Spanish)

`<home_or_commercial>` - Values from **Application** attribute set (e.g. 'Home', 'Commercial', or 'Classroom')

`<agronomic_crop>` - Values from **Agronomic Crop** attribute set

`<business_topic>` - Values from **Business Topic** attribute set

`<continuing_education_credits>` - Type of **Continuing Education Credits** offered by Events in the Event Group

`<cow_age_lactation_stage>` - Values from **Cow Age or Lactation Stage** attribute set

`<cover_crop>` - Values from **Cover Crop** attribute set

`<disaster>` - Values from **Disaster** attribute set

`<energy_source>` - Values from **Energy Source** attribute set

`<farm_structure>` - Values from **Farm Equipment/Structure** attribute set

`<food_type>` - Values from **Food Type** attribute set

`<forage_crop>` - Values from **Forage Crop** attribute set

`<fruit>` - Values from **Fruit** attribute set

`<industry>` - Values from **Industry** attribute set

`<insect_pests>` - Values from **Insect Pests** attribute set

`<plant_diseases>` - Values from **Plant Diseases** attribute set

`<plant_type>` - Values from **Plant Type** attribute set

`<poultry_flock_size>` - Values from **Poultry Flock Size** attribute set

`<turfgrass>` - Values from **Turfgrass/Lawn** attribute set

`<vegetable>` - Values from **Vegetable** attribute set

`<water_source>` - Values from **Water Source** attribute set

`<weeds>` - Values from **Weeds** attribute set


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

### Features on Category Landing Pages

`<is_featured_product_l1>` - Boolean, featured on L1 landing page

`<is_featured_product_l2>` - Boolean, featured on L2 landing page

`<is_featured_product_l3>` - Boolean, featured on L3 landing page

`<iwd_featured_product>` - Boolean, featured on L2 landing page

### Plone Information

`<plone_id>` - Plone Unique ID for item. This *is* a globally unique value.

`<plone_status>` - Plone workflow state (e.g., 'published', 'expired')

`<plone_url>` - URL for the content in the current Plone site

`<original_plone_ids>` - Plone Ids of content in the old (pre-import) site

`<original_plone_site>` - Hostname of the old (pre-import) Plone site


### Lead Image

Items can contain a lead image and image caption.

`<has_lead_image>` - Does this object have a lead image? (true or false)

`<include_lead_image>` - Show the lead image on the product page (true or false)

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
        "data" : "[Binary image data]",
    }

### Gated Content

`<is_gated_content>` - Boolean value of `true` if this is gated content
`<gated_url>` - URL of the gated opt-in form

### Exclude from sitemap and hide from search engines.

This attribute sets noindex and nofollow, and excludes a product from the sitemap.

`<am_hide_from_html_sitemap>` - Boolean value of `true` if this product should be hidden. Legacy Magento 1 value.

#### Maps to corresponding SEO settings in Magento 2

 * `<in_html_sitemap>`
 * `<in_xml_sitemap>`
 * `<meta_robots>`

### Omit Products

`<omit_magento>True</omit_magento>` - Omit product from Magento