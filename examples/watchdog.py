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