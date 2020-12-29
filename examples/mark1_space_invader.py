from ovos_utils.enclosure.mark1.faceplate.cellular_automaton import \
    SpaceInvader
from ovos_utils.messagebus import get_mycroft_bus
from time import sleep

bus = get_mycroft_bus("192.168.1.70")

game_of_life = SpaceInvader(bus=bus)

for grid in game_of_life:
    grid.display(invert=False)
    sleep(2)
