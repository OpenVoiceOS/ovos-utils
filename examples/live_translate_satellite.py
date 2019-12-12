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