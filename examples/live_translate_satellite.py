from jarbas_utils.messagebus import get_mycroft_bus, listen_for_message
from jarbas_utils import wait_for_exit_signal
from jarbas_utils.lang.translate import say_in_language

# from jarbas_utils.lang.translate import translate_to_mp3
# from jarbas_utils.sound import play_mp3

bus_ip = "0.0.0.0"  # enter a remote ip here, remember bus is unencrypted! careful with opening firewalls
bus = get_mycroft_bus(host=bus_ip)

TARGET_LANG = "pt"


def translate(message):
    utterance = message.data["utterance"]
    say_in_language(utterance, lang=TARGET_LANG)  # will play .mp3 directly

    # if you need more control
    # path = translate_to_mp3(utterance, lang=TARGET_LANG)
    # play_mp3(path, cmd="play %1")  # using sox


listen_for_message("speak", translate, bus=bus)


wait_for_exit_signal()  # wait for ctrl+c

bus.remove_all_listeners("speak")
bus.close()
