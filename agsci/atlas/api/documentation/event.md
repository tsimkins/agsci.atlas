# Event API Documentation

## Basic Event Details (All Event Types)

`<event_start_date>` - Start date/time of event

`<event_end_date>` - End date/time of event

`<event_agenda>` - Agenda for event (separate from body text field of `<description>`)

`<parent_id>` - Plone UID of the parent Workshop Group/Webinar Group to which the event belongs.

`<audience>` - Who is this for?

`<knowledge>` - What will you learn?

`<skill_level>` - Skill Level  (Beginner, Intermediate, Advanced)


## Location (Workshops and Conferences)

`<venue>` - Event venue name

`<address>` - Street address

`<city>` - City

`<state>` - State

`<zip>` - ZIP Code

`<county>` - County (used for aggregating to county event listings)

`<map_link>` - URL for directions to event venue (e.g. Google Maps)


## Location (Webinar)

`<webinar_url>` - The URL of the live webinar (used for upcoming webinars)


## Registration Information (All Event Types)

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


## Webinar Recording (Webinars Only)

`<webinar_recorded_url>` - The URL of the recorded webinar

`<webinar_recorded_files>` - A list of files (**Webinar Handouts** and **Webinar Presentations**) uploaded to accompany the **Webinar Recording**.
