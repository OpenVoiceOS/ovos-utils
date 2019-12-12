# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0]  - 2019-12-12

First public release

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

[unreleased]: https://github.com/JarbasAl/jarbas_utils/tree/dev
[0.3.0]: https://github.com/JarbasAl/jarbas_utils/tree/0.3
[0.2.3]: https://github.com/JarbasAl/jarbas_utils/tree/0.2
[0.1.1]: https://github.com/JarbasAl/jarbas_utils/tree/0.1
