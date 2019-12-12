# Jarbas - utils

collection of simple utilities for use across the mycroft ecosystem

* [Install](#install)
* [Usage](#usage)
    + [Messagebus](#messagebus)
    + [Configuration](#configuration)
        - [Wake words](#wake-words)
    + [Enclosures](#enclosures)
        - [System actions](#system-actions)
        - [Sound](#sound)
* [Changelog](#changelog)


## Install

stable version on pip 0.2.0

```bash
pip install jarbas_utils
```

dev version

```bash
pip install git+https://github.com/JarbasAl/jarbas_utils
```

## Usage

### Messagebus

The main way to interact with a mycroft instance is using the messagebus

    WARNING: the mycroft bus is unencrypted, be sure to secure your communications in some way before you start poking firewall ports open

Listening for events is super easy, here is a small program counting number of spoken utterances

```python
from jarbas_utils.messagebus import listen_for_message
from jarbas_utils.log import LOG
from jarbas_utils import wait_for_exit_signal

spoken = 0


def handle_speak(message):
    global spoken
    spoken += 1
    LOG.info("Mycroft spoke {n} sentences since start".format(n=spoken))


bus = listen_for_message("speak", handle_speak)
wait_for_exit_signal()  # wait for ctrl+c

# cleanup is a good practice! 
bus.remove_all_listeners("speak")
bus.close()
```

Triggering events in mycroft is also trivial

```python
from jarbas_utils.messagebus import send_message
from jarbas_utils.log import LOG
from jarbas_utils import create_daemon, wait_for_exit_signal
import random
from time import sleep


def alert():
    LOG.info("Alerting user of some event using Mycroft")
    send_message("speak", {"utterance": "Alert! something happened"})


def did_something_happen():
    while True:
        if random.choice([True, False]):
            alert()
        sleep(10)


create_daemon(did_something_happen) # check for something in background
wait_for_exit_signal()  # wait for ctrl+c
```

You can also connect to a remote messagebus, here is a live translator using language utils

```python
from jarbas_utils.messagebus import get_mycroft_bus, listen_for_message
from jarbas_utils import wait_for_exit_signal
from jarbas_utils.lang.translate import say_in_language


bus_ip = "0.0.0.0"  # enter a remote ip here, remember bus is unencrypted! careful with opening firewalls
bus = get_mycroft_bus(host=bus_ip)


TARGET_LANG = "pt"


def translate(message):
    utterance = message.data["utterance"]
    say_in_language(utterance, lang=TARGET_LANG)


listen_for_message("speak", translate, bus=bus)

wait_for_exit_signal()  # wait for ctrl+c

bus.remove_all_listeners("speak")
bus.close()
```

### Configuration

utils are provided to manipulate the user config

NOTE: this assumes you are running this code on the same machine as mycroft, it manipulates files directly in your system

```python
from jarbas_utils.configuration import read_mycroft_config

config = read_mycroft_config()
stt = config["stt"]["module"]
```

individual configs can also be manipulated
```python
from jarbas_utils.configuration import MycroftUserConfig, MycroftSystemConfig, MycroftDefaultConfig
from jarbas_utils.log import LOG

config = MycroftUserConfig()
config["lang"] = "pt"
config["tts"] = {"module": "google"}
config.store()

config = MycroftSystemConfig(allow_overwrite=True)
config["enclosure"] = {"platform": "respeaker"}
config.store()

config = MycroftDefaultConfig()
config.set_mycroft_root("~/PycharmProjects/mycroft-core")  # not needed for mark1/mark2/picroft
lang = config["lang"]
try:
    config["lang"] = "pt"
except PermissionError:
    LOG.error("config is read only")
```

you can also use the LocalConf class with your own path for other use cases
```python
from jarbas_utils.configuration import LocalConf

MY_CONFIG = "~/.projectX/projectX.conf"

class MyConfig(LocalConf):
    def __init__(self):
        super().__init__(MY_CONFIG)
        
config = MyConfig()
if not config.get("lang"):
    config["lang"] = "pt"
    config.store() # now changes are saved

config.merge({"host": "http://somedomain.net"})
config.reload() # now changes are gone

```

#### Wake words

when defining pocketsphinx wake words you often need to know the phonemes

```python
from jarbas_utils.configuration import update_mycroft_config
from jarbas_utils.lang.phonemes import get_phonemes


def create_wakeword(word, sensitivity):
    # sensitivity is a bitch to do automatically
    # IDEA make some web ui or whatever to tweak it experimentally
    phonemes = get_phonemes(word)
    config = {
        "listener": {
            "wake_word": word
          },
          word: {
            "andromeda": {
              "module": "pocketsphinx",
              "phonemes": phonemes,
              "sample_rate": 16000,
              "threshold": sensitivity,
              "lang": "en-us"
            }
          }
    }
    update_mycroft_config(config)
    
create_wakeword("andromeda", "1e-25")
        
```

Here is some sample output from get_phonemes

    hey mycroft HH EY1 . M Y K R OW F T
    hey chatterbox HH EY1 . CH AE T EH R B OW K S
    alexa AH0 L EH1 K S AH0


### Enclosures

If you are making a system enclosure you will likely need to handle system actions

#### System actions

```python
from jarbas_utils.system import system_reboot, system_shutdown, ssh_enable, ssh_disable
from jarbas_utils.log import LOG
from jarbas_utils.messagebus import get_mycroft_bus, Message


class MyEnclosureClass:

    def __init__(self):
        LOG.info('Setting up client to connect to a local mycroft instance')
        self.bus = get_mycroft_bus()
        self.bus.on("system.reboot", self.handle_reboot)
        
    def speak(self, utterance):
        LOG.info('Sending speak message...')
        self.bus.emit(Message('speak', data={'utterance': utterance}))
        
    def handle_reboot(self, message):
        self.speak("rebooting")
        system_reboot()
        
        
```
#### Sound

Volume control is also a common thing you need to handle

```python
from jarbas_utils.sound.alsa import AlsaControl
#from jarbas_utils.sound.pulse import PulseAudio
from jarbas_utils.log import LOG
from jarbas_utils.messagebus import get_mycroft_bus, Message


class MyPretendEnclosure:

    def __init__(self):
        LOG.info('Setting up client to connect to a local mycroft instance')
        self.bus = get_mycroft_bus()
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
        if self.alsa.is_muted():
            self.alsa.unmute()
        
    def handle_set_volume(self, message):
        volume = message.data.get("volume", 50)
        assert 0 <= volume <= 100
        self.alsa.set_volume(volume)

```

## Changelog

- 0.2.0
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
    - language utils
        - get_tts
        - translate_to_mp3
- 0.1.1
    - language utils
        - detect_language alternative using google services
            - make pycld2 optional
- 0.1.0
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
