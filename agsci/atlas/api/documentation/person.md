# Person API Documentation

## Listing all people in a directory

 * Calling the `@@api` view from the directory root will show a listing of all people in the directory.
 * Appending an `?updated=[seconds]` parameter to the URL will limit that data by the people who have been updated less than `[seconds]` seconds ago.
 * The `?bin=False` URL parameter can be used to prevent the individual's profile image from being shown.

## Name

Information about the individual's name and Penn State username (login.)

`<person_psu_user_id>` - Individual's Penn State username/login name (e.g. 'xyz123')

`<name>` - A system-generated full name (i.e. "[first_name] [middle_name] [last_name], [suffix]")

`<first_name>` - First name

`<middle_name>` - Middle name

`<last_name>` - Last name

`<suffix>` - Suffix (e.g. Jr., Ph.D., II, etc.)


## Contact Information

`<email_address>` - Email address ('xyz123@psu.edu')

`<office_phone>` - Office phone number ('814-555-1212')

`<fax_number>` - Office fax number ('814-555-1212')

`<venue>` - Office building name

`<address>` - Street address

`<city>` - City

`<state>` - State

`<zip_code>` - ZIP code


## Professional Information

`<expertise>` - List of specific areas of expertise (user provided) with each area as an `<item>` tag.

`<description>` - Rich text field containing biographical information

`<person_classification>` - Faculty, Staff, Educator, etc. with each classification as an `<item>` tag.

`<county>` - Counties that the individual is affiliated with (if county-based) with each county as an `<item>` tag.

`<education>` - List of degrees (e.g. 'Ph.D., The Pennsylvania State University, Generic Studies, 2001') with each degree as an individiual `<item>` tag.

`<person_job_title>` - Primary job title for individual

`<person_job_titles>` - List of job titles for individual


## Social Media

Links to individual's social media pages.

`<facebook_url>` - Facebook

`<google_plus_url>` - Google Plus

`<linkedin_url>` - LinkedIn

`<twitter_url>` - Twitter


## Portrait

`<leadimage>` - This data structure contains the individual's portrait
