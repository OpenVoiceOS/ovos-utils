# Jarbas - utils

collection of simple utilities for use across the mycroft ecosystem

- [Jarbas - utils](#jarbas---utils)
  * [Install](#install)
  * [Usage](#usage)
    + [Wake words](#wake-words)
  * [Enclosures](#enclosures)
    + [System actions](#system-actions)
    + [Sound](#sound)
  * [Changelog](#changelog)


## Install
```bash
pip install jarbas_utils
```

## Usage

### Wake words

when defining pocketsphinx wake words you often need to know the phonemes

```python
from jarbas_utils.lang.phonemes import get_phonemes

words = ["hey mycroft", "hey chatterbox", "alexa"]
for word in words:
    print(word, get_phonemes(word))
        
```

Here is some sample output

    hey mycroft HH EY1 . M Y K R OW F T
    hey chatterbox HH EY1 . CH AE T EH R B OW K S
    alexa AH0 L EH1 K S AH0

## Enclosures

If you are making a system enclosure you will likely need to handle system actions

### System actions

```python
from jarbas_utils.system import system_reboot, system_shutdown, ssh_enable, ssh_disable
from jarbas_utils.log import LOG
from mycroft_bus_client import MessageBusClient, Message



class MyEnclosureClass:

    def __init__(self):
        LOG.info('Setting up client to connect to a local mycroft instance')
        self.bus = MessageBusClient()
        self.bus.run_in_thread()
        self.bus.on("system.reboot", self.handle_reboot)
        
    def speak(self, utterance):
        LOG.info('Sending speak message...')
        self.bus.emit(Message('speak', data={'utterance': utterance}))
        
    def handle_reboot(self, message):
        self.speak("rebooting")
        system_reboot()
        
        
```
### Sound

Volume control is also a common thing you need to handle

```python
from jarbas_utils.sound.alsa import AlsaControl
#from jarbas_utils.sound.pulse import PulseAudio
from jarbas_utils.log import LOG
from mycroft_bus_client import MessageBusClient, Message


class MyPretendEnclosure:

    def __init__(self):
        LOG.info('Setting up client to connect to a local mycroft instance')
        self.bus = MessageBusClient()
        self.bus.run_in_thread()
        # None of these are mycroft signals, but you get the point
        self.bus.on("set.volume", self.handle_set_volume)
        self.bus.on("speak.volume", self.handle_speak_volume)
        self.bus.on("mute.volume", self.handle_mute_volume)
        self.bus.on("unmute.volume", self.handle_unmute_volume)
        
        self.alsa = AlsaControl()
        # self.pulse = PulseAudio()
        
    def speak(self, utterance):
        self.bus.emit(Message('speak', data={'utterance': utterance}))
        
    def handle_speak_volume(self, message):
        volume = self.alsa.get_volume()
        self.speak(volume)
        
    def handle_mute_volume(self, message):
        if not self.alsa.is_muted():
            self.alsa.mute()
        
    def handle_unmute_volume(self, message):
        if not self.alsa.is_muted():
            self.alsa.unmute()
        
    def handle_set_volume(self, message):
        volume = message.data.get("volume", 50)
        assert 0 <= volume <= 100
        self.alsa.set_volume(volume)

```

## Changelog

- 0.1.1
    - language utils
        - add detect_language alternative using google services
        - make pycld2 optional
- 0.1.0
    - language utils
        - get_phonemes
        - detect_language
        - translate
    -  sound utils
        - play_wav
        - play_mp3
        - play_ogg
        - AlsaControl
        - PulseControl
    - system utils
        - reboot
        - shutdown
        - enable/disable ssh
        - ntp sync