# Event API Documentation

## Event Platforms

Events can originate in either Plone (simple events) or Cvent (complex events.)  The `<product_platform>` field documents which platform the event originated in.

Since the events originating in Cvent don't have an explicit type (i.e. Workshop, Conference, or Webinar)  this must be set in Plone using the `<event_type>` field.  This manual setting will be used to determine the `<education_format>` and `<attribute_set>` tags in the API export.  The `<product_type>` tag will be `Cvent Event`.

In most cases, Cvent events will be of the **Workshop** or **Conference** type.

## Basic Event Details (All Event Types)

`<event_start_date>` - Start date/time of event

`<event_end_date>` - End date/time of event

`<parent_id>` - `plone_id` of the parent Workshop Group/Webinar Group to which the event belongs.

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<skill_level>` - Skill Level  (Beginner, Intermediate, Advanced)

## Product Page Note

`<product_page_note>` - Short text to be featured in a callout on the product page.

### Event Agenda

The agenda for event is presented as a structure of `<item>` tags, each containing a time, title, and description.

#### Examples

##### XML

    <event_agenda>
        <item>
            <time>9:00 a.m.</time>
            <title>Introduction</title>
            <description>Speaker 1</description>
        </item>
        <item>
            <time>9:30 a.m.</time>
            <title>Session 1: Topic A</title>
            <description>Speaker 2 and Speaker 3</description>
        </item>
    </event_agenda>

##### JSON

    "event_agenda": [
        {
            "description": "Speaker 1",
            "time": "9:00 a.m.",
            "title": "Introduction"
        },
        {
            "description": "Speaker 2 and Speaker 3",
            "time": "9:30 a.m.",
            "title": "Session 1: Topic A"
        }
    ],

### Event Credits/CEU

#### Examples

##### XML

    <credits>
        <item>
            <credit_type>Credit Type 1</credit_type>
            <credit_category>Credit Category 2</credit_category>
            <credit_value>1.5</credit_value>
        </item>
        <item>
            <credit_type>Credit Type 2</credit_type>
            <credit_category>Credit Category 3</credit_category>
            <credit_value>2.0</credit_value>
        </item>
    </credits>

##### JSON

    "credits": [
        {
            "credit_category": "Credit Category 2",
            "credit_type": "Credit Type 1",
            "credit_value": "1.50"
        },
        {
            "credit_category": "Credit Category 3",
            "credit_type": "Credit Type 2",
            "credit_value": "2.00"
        }
    ],

## Location (Plone Workshop and Plone Conference)

Note: Cvent events in Plone will also have these fields, but this is informational only.

`<venue>` - Event venue name

`<address>` - Street address as a list/array of address lines. In the XML output, this is a structure containing one or more `<item>` tags. In the JSON output, it's an array.

`<city>` - City

`<state>` - State

`<zip>` - ZIP Code

`<county>` - County in which the event is taking place.  Note that even though only one county may be selected for an event, the county is inside an `<item>` tags inside the `<county>` tag to be consistent with other instances of this attribute.

`<map_link>` - URL for directions to event venue (e.g. Google Maps)

### Examples

#### XML

    <venue>Penn Stater Hotel And Conference Center</venue>

    <address>
        <item>215 Innovation Boulevard</item>
        <item>Executive Conference Room #42</item>
    </address>

    <city>State College</city>

    <state>PA</state>

    <zip>16803</zip>

    <county>
        <item>Centre</item>
    </county>

    <map_link>https://goo.gl/maps/NvXxRNW94uT2</map_link>


#### JSON

    "venue": "Penn Stater Hotel And Conference Center",

    "address": [
        "215 Innovation Boulevard",
        "Executive Conference Room #42"
    ],

    "city": "State College",

    "state": "PA",

    "zip": "16803"

    "county": [
        "Centre"
    ],

    "map_link": "https://goo.gl/maps/NvXxRNW94uT2",

## Location (Plone Webinar)

`<webinar_url>` - The URL of the live webinar (used for upcoming webinars)


## Registration Information (Plone Workshops, Webinars, and Conferences)

`<event_registration_help_name>` - Registration help contact's name

`<event_registration_help_email>` - Registration help contact's email address

`<event_registration_help_phone>` - Registration help contact's phone number

`<event_registrant_type>` - Participant, Vendor, Volunteer, etc.

`<registration_deadline>` - Date on which registrations will no longer be accepted

`<event_registration_status>` - Open or Closed

`<cancelation_deadline>` - Deadline to cancel a registration

`<event_capacity>` - Maximum number of people that can register for this event

`<event_walkin>` - Are walkins accepted?

`<price>` - Price for event registration

`<available_to_public>` - This event is open to registration by anyone. Either True or False.

`<youth_event>` - This event is intended for youth. Either True or False.


## Registration Form Fields

>
> **DRAFT**
>

Notes:

 * For Workshops/Webinars that are part of a Workshop/Webinar Group, these fields are set
at the Group level, and not at the individual event level.

 * For standalone Workshops/Webinars, these fields are set at the individual Workshop/Webinar level.

 * These fields are not set on Cvent events.

The `<registration_fields>` structure is used to define the fields used in the event
registration form in Magento.  It consists of multiple `<item>` tags, with potential attributes of:

  * `<token>` - A string that uniquely identifies the field.  This is generally a normalized version of the field title (e.g. "job_title" for the "Job Title" field) and should not be changed even if the field title is changed.

  * `<type>` - Either the name of the field for basic registration fields (e.g. `firstname`) or `field` for additional fields.  *DRAFT: Also, `checkbox` was in the spec. (We need more definition around those types.)*

  * `<title>` - The title or label of the field.

  * `<is_require>` - If field is required on registration form.  Boolean values.

  * `<is_visitor_option>` - If this field will be part of the registration form. Boolean value, always True.

  * `<options>` - List of options for select or multiselect fields. Presented as a list of `<item>` tags, each containing a `<token>` and `<title>` tag.

  * `<sort_order>` - Numerical sort order from 0..n for field order in form.


### XML

    <registration_fields>

        <item>
            <token>firstname</token>
            <sort_order>0</sort_order>
            <is_visitor_option>True</is_visitor_option>
            <is_require>False</is_require>
            <title>First Name</title>
            <type>firstname</type>
        </item>

        ...

        <item>
            <token>primary_phone_type</token>
            <sort_order>4</sort_order>
            <is_visitor_option>True</is_visitor_option>
            <is_require>False</is_require>
            <title>Primary Phone Type</title>
            <type>primary_phone_type</type>
            <options>
                <item>
                    <token>home</token>
                    <title>Home</title>
                </item>
                <item>
                    <token>work</token>
                    <title>Work</title>
                </item>
                <item>
                    <token>mobile</token>
                    <title>Mobile</title>
                </item>
            </options>
        </item>

        ...

        <item>
            <token>job_title</token>
            <sort_order>6</sort_order>
            <is_visitor_option>True</is_visitor_option>
            <is_require>False</is_require>
            <title>Job Title</title>
            <type>field</type>
        </item>

        <item>
            <token>accessibility</token>
            <sort_order>7</sort_order>
            <is_visitor_option>True</is_visitor_option>
            <is_require>False</is_require>
            <title>Do you require assistance?</title>
            <type>checkbox</type>
            <options>
                <item>
                    <token>audio</token>
                    <title>Audio</title>
                </item>
                <item>
                    <token>visual</token>
                    <title>Visual</title>
                </item>
                <item>
                    <token>mobile</token>
                    <title>Mobile</title>
                </item>
            </options>
        </item>

        ...

    </registration_fields>

### JSON

    "registration_fields": [
        {
            "is_require": false,
            "is_visitor_option": true,
            "sort_order": 0,
            "title": "First Name",
            "token": "firstname",
            "type": "firstname"
        },

        ...

        {
            "is_require": false,
            "is_visitor_option": true,
            "options": [
                {
                    "title": "Home",
                    "token": "home"
                },
                {
                    "title": "Work",
                    "token": "work"
                },
                {
                    "title": "Mobile",
                    "token": "mobile"
                }
            ],
            "sort_order": 4,
            "title": "Primary Phone Type",
            "token": "primary_phone_type",
            "type": "primary_phone_type"
        },

        ...

        {
            "is_require": false,
            "is_visitor_option": true,
            "sort_order": 6,
            "title": "Job Title",
            "token": "job_title",
            "type": "field"
        },

        {
            "is_require": false,
            "is_visitor_option": true,
            "options": [
                {
                    "title": "Audio",
                    "token": "audio"
                },
                {
                    "title": "Visual",
                    "token": "visual"
                },
                {
                    "title": "Mobile",
                    "token": "mobile"
                }
            ],
            "sort_order": 7,
            "title": "Do you require assistance?",
            "token": "accessibility",
            "type": "checkbox"
        }

        ...

    ],

## Ticket Type

This is associated with the registration fields, and sets the types of tickets
available for the event.  It currently provides no actual types, since those
will be set in Magento.

### XML

    <ticket_type>

        <is_ticket_option>True</is_ticket_option>

        <is_require>False</is_require>

        <title>ticket type</title>

    </ticket_type>

### JSON

    "ticket_type": {
        "is_require": false,
        "is_ticket_option": true,
        "title": "ticket type"
    },

## Cvent Event Fields

`<cvent_id>` - Unique identifier GUID (e.g. 'A24E841C-9FD3-4F21-A0C5-EEC710B1F43F') for the Cvent event.

`<cvent_url>` - Link to the Cvent event summary page.

`<event_type>` - Type of event (Workshop, Conference, or Webinar)

`<external_url>` - Link to the Cvent event registration page.

### Sessions

`<product_detail>` - List of data for Cvent event sessions, one session per `<item>`

Each `<item>` inside `<product_detail>` can have the following fields:

`<capacity>` - Number of individuals permitted at the session

`<educational_content>` - Is educational content (a flag to report on within Cvent)

`<end_time>` - End time of session

`<is_included>` - Is Included

`<magento_agenda>` - Include on Magento Agenda

`<product_code>` - "SKU" - not used in Cvent, but could be used for rollup summery reporting of that product

`<product_description>` - HTML description

`<product_id>` - GUID, unique to session

`<product_name>` - Session name

`<product_type>` - Type of session (Admission Item, Donation Item, Group Item, Quantity item, Quantity, Session, Track)

`<session_category_id>` - All sessions have a GUID. If a session isn't within a group, it has a value of `00000000-0000-0000-0000-000000000000`

`<session_category_name>` - Name of session category

`<start_time>` - Start time of session

`<status>` - Status of session (Active, Cancelled, Closed)

#### Examples

##### XML

	<product_detail>
		<item>
			<capacity>...</capacity>
			<educational_content>...</educational_content>
			<end_time>...</end_time>
			<is_included>...</is_included>
			<magento_agenda>...</magento_agenda>
			<product_code>...</product_code>
			<product_description>...</product_description>
			<product_id>...</product_id>
			<product_name>...</product_name>
			<product_type>...</product_type>
			<session_category_id>...</session_category_id>
			<session_category_name>...</session_category_name>
			<start_time>...</start_time>
			<status>...</status>
		</item>
	</product_detail>

##### JSON			

    "product_detail": [
        {
            "capacity": "...", 
            "educational_content": "...", 
            "end_time": "...", 
            "is_included": "...", 
            "magento_agenda": "...", 
            "product_code": "...", 
            "product_description": "...", 
            "product_id": "...", 
            "product_name": "...", 
            "product_type": "...", 
            "session_category_id": "...", 
            "session_category_name": "...", 
            "start_time": "...", 
            "status": "..."
        }
    ], 

## Webinar Recording (Plone Webinars)

`<webinar_recorded_url>` - The URL of the recorded webinar

`<duration_formatted>` - Duration of the webinar, formatted as HH:MM:SS

`<transcript>` - Plain text transcript of webinar

`<related_download_product_ids>` - List of `<item>` tags containing the `plone_id` of the webinar recording.  This is used as a key for the webinar recording product in Magento.

`<webinar_recorded_files>` - A list of files (**Webinar Handouts** and **Webinar Presentations**) uploaded to accompany the **Webinar Recording**.

`<length_content_access>` - Length of content access for webinar recording

`<watch_now>` - Public can watch webinar recording rather than having to purchase. Possible values of True/False.

### Examples

#### XML

    <duration_formatted>00:20:30</duration_formatted>

    ...

    <transcript>This is
    a transcript
    of the webinar.
    </transcript>

    ...

    <webinar_recorded_files>
        <item>
            <file>
                <mimetype>application/pdf</mimetype>
                <data>...</data>
            </file>
            <product_type>Webinar Presentation</product_type>
            <name>Slides for Sample Webinar</name>
            <short_name>slides-for-sample-webinar</short_name>
            <plone_id>...</plone_id>
            <updated_at>...</updated_at>
            <cksum>...</cksum>
            <short_description>Slides for Sample Webinar Description</short_description>
        </item>
        <item>
            <file>
                <mimetype>application/pdf</mimetype>
                <data>...</data>
            </file>
            <product_type>Webinar Handout</product_type>
            <name>Sample Webinar Handout</name>
            <short_name>sample-webinar-handout</short_name>
            <plone_id>...</plone_id>
            <updated_at>...</updated_at>
            <cksum>...</cksum>
            <short_description>Sample Webinar Handout Description</short_description>
        </item>
    </webinar_recorded_files>
    <webinar_recorded_url>https://meeting.psu.edu/xxxyyzzz123/</webinar_recorded_url>

#### JSON

    "duration_formatted": "00:20:30",

    ...

    "transcript": "This is\r\na transcript\r\nof the webinar.",

    ...

    "webinar_recorded_files": [
        {
            "cksum": "...",
            "file": {
                "data": "...",
                "mimetype": "application/pdf"
            },
            "name": "Slides for Sample Webinar",
            "plone_id": "da18d99c00164b668af4d265c139bf09",
            "product_type": "Webinar Presentation",
            "short_description": "Slides for Sample Webinar Description",
            "short_name": "slides-for-sample-webinar",
            "updated_at": "..."
        },
        {
            "cksum": "...",
            "file": {
                "data": "...",
                "mimetype": "application/pdf"
            },
            "name": "Sample Webinar Handout",
            "plone_id": "...",
            "product_type": "Webinar Handout",
            "short_description": "Sample Webinar Handout Description",
            "short_name": "sample-webinar-handout",
            "updated_at": "..."
        }
    ],

    "webinar_recorded_url": "https://meeting.psu.edu/xxxyyzzz123/",
