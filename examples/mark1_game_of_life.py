from ovos_utils.enclosure.mark1.faceplate.cellular_automaton import GoL
from ovos_utils.messagebus import get_mycroft_bus

bus = get_mycroft_bus("192.168.1.70")


game_of_life = GoL(bus=bus)


def handle_new_frame(grid):
    grid.display(invert=False)


game_of_life.run(0.5, handle_new_frame)