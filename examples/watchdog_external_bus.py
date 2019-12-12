from jarbas_utils.messagebus import send_message, get_mycroft_bus
from jarbas_utils.log import LOG
from jarbas_utils import create_daemon, wait_for_exit_signal
from jarbas_utils.sound import play_wav
import random
from time import sleep


bus_ip = "0.0.0.0"  # enter a remote ip here, remember bus is unencrypted! careful with opening firewalls
bus = get_mycroft_bus(host=bus_ip)


def alert():
    LOG.info("Alerting user of some event using Mycroft")
    send_message("speak", {"utterance": "Alert! something happened"}, bus=bus)


def did_something_happen():
    while True:
        if random.choice([True, False]):
            play_wav("alert.wav")
            alert()
        sleep(10)


create_daemon(did_something_happen) # check for something in background
wait_for_exit_signal()  # wait for ctrl+c