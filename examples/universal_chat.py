from ovos_utils.messagebus import send_message, listen_for_message
from ovos_utils.lang.translate import translate_text
from ovos_utils.lang.detect import detect_lang
from ovos_utils.log import LOG


OUTPUT_LANG = "pt"  # received messages will be in this language
MYCROFT_LANG = "en"  # mycroft is configured in this language


def handle_speak(message):
    utt = message.data["utterance"]
    utt = translate_text(utt, "pt")  # source lang is auto detected
    print("MYCROFT:", utt)


bus = listen_for_message("speak", handle_speak)

print("Write in any language and mycroft will answer in {lang}".format(lang=OUTPUT_LANG))


while True:
    try:
        utt = input("YOU:")
        lang = detect_lang("utt")   # source lang is auto detected, this is optional
        if lang != MYCROFT_LANG:
            utt = translate_text(utt)
        send_message("recognizer_loop:utterance",
                     {"utterances": [utt]},
                     bus=bus # re-utilize the bus connection
                     )
    except KeyboardInterrupt:
        break
    except Exception as e:
        LOG.exception(e)

bus.remove_all_listeners("speak")
bus.close()
