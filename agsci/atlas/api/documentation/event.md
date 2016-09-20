# Event API Documentation

## Event Platforms

Events can originate in either Plone (simple events) or Cvent (complex events.)  The `<product_platform>` field documents which platform the event originated in.

Since the events originating in Cvent don't have an explicit type (i.e. Workshop, Conference, or Webinar)  this must be set in Plone using the **Event Type** field.  This manual setting will be reflected in the `<product_type>` tag in the API export.

In most cases, Cvent events will be of the **Workshop** or **Conference** type.

## Basic Event Details (All Event Types)

`<event_start_date>` - Start date/time of event

`<event_end_date>` - End date/time of event

`<parent_id>` - `plone_id` of the parent Workshop Group/Webinar Group to which the event belongs.

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<skill_level>` - Skill Level  (Beginner, Intermediate, Advanced)

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

`<address>` - Street address

`<city>` - City

`<state>` - State

`<zip>` - ZIP Code

`<county>` - County in which the event is taking place.  Note that even though only one county may be selected for an event, the county is inside an `<item>` tags inside the `<county>` tag to be consistent with other instances of this attribute.

`<map_link>` - URL for directions to event venue (e.g. Google Maps)


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


## Webinar Recording (Plone Webinars)

`<webinar_recorded_url>` - The URL of the recorded webinar

`<duration_formatted>` - Duration of the webinar, formatted as HH:MM:SS

`<transcript>` - Plain text transcript of webinar

`<webinar_recorded_files>` - A list of files (**Webinar Handouts** and **Webinar Presentations**) uploaded to accompany the **Webinar Recording**.
