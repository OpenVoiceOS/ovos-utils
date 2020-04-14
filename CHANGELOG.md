# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

current dev branch

## [0.6.1] - 2020 - 04 -14

Parsing, cellular automaton and Mark1 animations

### Added

- jarbas_utils.parse
    - remove_parentheses
    - summarize
    - singularize
    - extract_sentences
    - extract_paragraphs
- enclosure base class
- mark1 animation utils
- mark1 animations
    - langton's ant
    - sierpinski triangle
    - rule 110
    - square wave
    - particle box
    - particle shooter
- mark1 icons
    - music icon
    - hearth icon
    - hollow hearth icon
    - skull icon
    - deadfish icon
    - info icon
    - arrow left icon
    - warning icon
    - cross icon
    - JarbasAI logo icon
    - SpaceInvader icons
    
### Changed

- moved mark1 faceplate classes around
- moved fuzzy matching util to jarbas_utils.parse

### Fixed

- mark1
    - hardcoded width/height for padding in decode

## [0.5.1] - 2020 - 02 -04

### Fixed

- security
  -   cast encryption key to bytes

## [0.5.0]

Intents, colours and crypto


### Added

- utils
    - camel_case_split
    - colors
    - crypto utils
        - encrypt
        - decrypt
        - generate_key

- intents
  -   IntentAPI
    - IntentLayers
    - BaseIntentEngine
    
- skills
    - IntentEngineSkill
    
## [0.4.1]  - 17-01-2020

### Fixed

setup.py install

## [0.4.0]  - 17-01-2020


### Added

- skills
    - universal skill
    - universal fallback
 
- signal
    - get_ipc_directory
    - ensure_directory_exists
    - create_file
    - create_signal
    - check_for_signal
       
- general utils
    - create_loop
    - resolve_resource_file
    - get_mycroft_root
    - get_handler_name

- sound
    - is_speaking
    - wait_while_speaking
    
- security utils
    - create self signed certificate

- system utils
    - get_desktop_environment
    - is_process_running

- messagebus utils
    - BusQuery
    - BusService
    - BusFeedProvider
    - BusFeedConsumer
    
- mark1
    - FaceplateGrid 
    - FaceplateAnimation
    - game of life
 
### Fixed

- support mark1/2 user config path under mycroft user
- reading config


### Changed

- remove all database utils, moved to https://github.com/OpenJarbas/json_database

## [0.3.2]  - 2019-12-12

quick bugfix for pipy package

### Added

- json utils
    - is_jsonifiable

### Fixed

- json utils
    - get_XX_recursively list comprehension
        - fixes search_XX in JsonDatabase
    
## [0.3.1]  - 2019-12-12

First public release under OpenJarbas 

## [0.3.0]  - 2019-12-12

Released on [pypi](https://pypi.org/project/jarbas-utils/)

### Added

- ssml utils
    - ssml builder class
- xml utils
    - xml2dict
    - dict2xml

### Fixed

- database utils
    - mutating source list on jsonify_recursively
    
### Changed

- moved functions around to json_helper

## [0.2.3]

### Added

 - database utils
    - jsonify_recursively
    - pretty print method
        
### Fixed

 - database utils
    - fix saving of db containing custom classes
    
## [0.2.2]

### Added

- database utils
    - allow custom classes as database items
        
        
## [0.2.1]

### Added

- database utils
    - allow filtering empty values on JsonDatabase key search
        
### Fixed

- configuration util
    - bugfix/ expand paths with ~
        
## [0.2.0]

### Added

- generic utils
    - create_daemon
    - wait_for_exit_signal
- messagebus utils
    - get_mycroft_bus
    - listen_for_message
    - listen_once_for_message
    - wait_for_reply
    - send_message
- configuration utils
    - read_mycroft_config
    - update_mycroft_config
    - json / dictionary utils
- database utils
    - json database (search and storage)
    - fuzzy match
- language utils
    - get_tts
    - translate_to_mp3

## [0.1.1]

### Changed

- language utils
    - detect_language alternative using google services
        - make pycld2 optional

## [0.1.0]

### Added

- language utils
    - get_phonemes
    - detect_language
    - translate
    - say_in_language
-  sound utils
    - play_wav
    - play_mp3
    - play_ogg
    - record
    - AlsaControl
    - PulseControl
- system utils
    - reboot
    - shutdown
    - enable/disable ssh
    - ntp sync

[unreleased]: https://github.com/OpenJarbas/jarbas_utils/tree/dev
[0.6.1]: https://github.com/OpenJarbas/jarbas_utils/tree/0.6
[0.5.0]: https://github.com/OpenJarbas/jarbas_utils/tree/0.5
[0.4.1]: https://github.com/OpenJarbas/jarbas_utils/tree/0.4
[0.3.2]: https://github.com/OpenJarbas/jarbas_utils/tree/0.3
