#!/usr/bin/env python3
# each method here is a console_script defined in setup.py
# each corresponds to a cli util
from ovos_bus_client import MessageBusClient, Message
from ovos_config import Configuration
import sys


def ovos_speak():
    if (args_count := len(sys.argv)) == 2:
        utt = sys.argv[1]
        lang = Configuration().get("lang", "en-us")
    elif args_count == 3:
        utt = sys.argv[1]
        lang = sys.argv[2]
    else:
        print("USAGE: ovos-speak {utterance} [lang]")
        raise SystemExit(2)
    client = MessageBusClient()
    client.run_in_thread()
    client.emit(Message("speak", {"utterance": utt, "lang": lang}))
    client.close()


def ovos_say_to():
    if (args_count := len(sys.argv)) == 2:
        utt = sys.argv[1]
        lang = Configuration().get("lang", "en-us")
    elif args_count == 3:
        utt = sys.argv[1]
        lang = sys.argv[2]
    else:
        print("USAGE: ovos-say-to {utterance} [lang]")
        raise SystemExit(2)
    client = MessageBusClient()
    client.run_in_thread()
    client.emit(Message("recognizer_loop:utterance", {"utterances": [utt], "lang": lang}))
    client.close()


def ovos_listen():
    client = MessageBusClient()
    client.run_in_thread()
    client.emit(Message("mycroft.mic.listen"))
    client.close()
