from ovos_utils.skills.settings import get_all_remote_settings, get_remote_settings

""" 
WARNING: selene backend does not use a proper skill_id, if you have
skills with same name but different author settings will overwrite each
other on the backend

2 way sync with Selene is also not implemented and causes a lot of issues, 
these problems have been reported over 9 months ago (and counting)

I strongly recommend you validate returned data as much as possible, 
maybe ask the user to confirm any action, DO NOT automate settings sync

skill matching is currently done by checking "if {skill} in string"
once mycroft fixes it on their side this will start using a proper
unique identifier

THIS METHOD IS NOT ALWAYS SAFE
"""

# get raw skill settings payload
all_remote_settings = get_all_remote_settings()
"""
{'@0e813c09-8dbc-40ed-974c-5705274a7b55|mycroft-npr-news|20.08': {'custom_url': '',
                                                                  'station': 'not_set',
                                                                  'use_curl': True},
 '@0e813c09-8dbc-40ed-974c-5705274a7b55|mycroft-pairing|20.08': None,
 '@0e813c09-8dbc-40ed-974c-5705274a7b55|mycroft-volume|20.08': {'ducking': True},
 (...)
 'mycroft-weather|20.08': {'units': 'default'},
 'mycroft-wiki|20.08': None}
"""

# search remote settings for a specific skill
voip_remote_settings = get_remote_settings("skill-voip")
"""
{'add_contact': False,
 'auto_answer': True,
 'auto_reject': False,
 'auto_speech': 'I am busy, call again later',
 'contact_address': 'user@sipxcom.com',
 'contact_name': 'name here',
 'delete_contact': False,
 'gateway': 'sipxcom.com',
 'password': 'SECRET',
 'sipxcom_gateway': 'https://sipx.mattkeys.net',
 'sipxcom_password': 'secret',
 'sipxcom_sync': False,
 'sipxcom_user': 'MattKeys',
 'user': 'user'}
"""