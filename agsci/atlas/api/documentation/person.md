Person API Documentation
========================

`<username>` - Individual's Penn State username/login name (e.g. 'xyz123')

`<name>` - Structure containing information about the individual's name:

  * `<first>` - First name
  * `<middle>` - Middle name
  * `<last>` - Last name
  * `<suffix>` - Suffix (e.g. Jr., Ph.D., II, etc.)

`<contact>` - Contact information for the individual, containing:

  * `<email_address>` - Email address ('xyz123@psu.edu')
  * `<phone>` - Office phone number ('814-555-1212')
  * `<fax_number>` - Office fax number ('814-555-1212')
  * `<venue>` - Office building name
  * `<address>` - Street address
  * `<city>` - City
  * `<state>` - State
  * `<zip_code>` - ZIP code

`<professional>` - Professional information for the user, including:

  * `<areas_expertise>` - List of specific areas of expertise (user provided)
  * `<bio>` - Rich text field containing biographical information
  * `<classifications>` - Faculty, Staff, Educator, etc.
  * `<counties>` - Counties that the individual is affiliated with (if county-based)
  * `<education>` - List of degrees (e.g. 'Ph.D., The Pennsylvania State University, Generic Studies, 2001')
  * `<job_titles>` - List of job titles for individual

`<social_media>` - Links to individual's social media pages

 * `<facebook_url>` - Facebook
 * `<google_plus_url>` - Google Plus
 * `<linkedin_url>` - LinkedIn
 * `<twitter_url>` - Twitter

Additional notes:

 * The `<title>` for a person contains a system-generated full name
 * The `<leadimage>` data structure contains the individual's portrait
