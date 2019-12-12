from jarbas_utils.messagebus import listen_for_message
from jarbas_utils.log import LOG
from jarbas_utils import wait_for_exit_signal

heard = 0
spoken = 0


def handle_speak(message):
    global spoken
    spoken += 1
    LOG.info("Mycroft spoke {n} sentences since start".format(n=spoken))


def handle_hear(message):
    global heard
    heard += 1
    LOG.info("Mycroft responded to {n} sentences since start".format(n=heard))


bus = listen_for_message("speak", handle_speak)
listen_for_message("recognize_loop:utterance", handle_hear, bus=bus)  # re utilize bus

wait_for_exit_signal()  # wait for ctrl+c

# cleanup is a good practice!
bus.remove_all_listeners("speak")
bus.remove_all_listeners("recognize_loop:utterance")
bus.close()
