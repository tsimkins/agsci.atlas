# Event API Documentation

## Event Platforms

Events can originate in either Plone (simple events) or Cvent (complex events.)  The `<product_platform>` field documents which platform the event originated in.

Since the events originating in Cvent don't have an explicit type (i.e. Workshop, Conference, or Webinar)  this must be set in Plone using the **Event Type** field.  This manual setting will be reflected in the `<product_type>` tag in the API export.

In most cases, Cvent events will be of the **Workshop** or **Conference** type. 

## Basic Event Details (All Event Types)

`<event_start_date>` - Start date/time of event

`<event_end_date>` - End date/time of event

`<event_agenda>` - Agenda for event (separate from body text field of `<description>`)

`<parent_id>` - `plone_id` of the parent Workshop Group/Webinar Group to which the event belongs.

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<skill_level>` - Skill Level  (Beginner, Intermediate, Advanced)


## Location (Plone Workshop and Plone Conference)

Note: Cvent events in Plone will also have these fields, but this is informational only.

`<venue>` - Event venue name

`<address>` - Street address

`<city>` - City

`<state>` - State

`<zip>` - ZIP Code

`<county>` - County (used for aggregating to county event listings)

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


## Webinar Recording (Plone Webinars)

`<webinar_recorded_url>` - The URL of the recorded webinar

`<duration_formatted>` - Duration of the webinar, formatted as HH:MM:SS

`<transcript>` - Plain text transcript of webinar

`<webinar_recorded_files>` - A list of files (**Webinar Handouts** and **Webinar Presentations**) uploaded to accompany the **Webinar Recording**.
