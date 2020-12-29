from ovos_utils.enclosure.mark1.faceplate.icons import HollowHeartIcon, \
    HeartIcon, SkullIcon, Boat
from ovos_utils.enclosure.mark1.faceplate.animations import LeftRight, \
    HorizontalScroll


class SailingBoat(Boat, HorizontalScroll):
    pass


class MovingHeart(HeartIcon, LeftRight):
    pass


class MovingHeart2(HollowHeartIcon, LeftRight):
    pass


class MovingSkull(SkullIcon, LeftRight):
    pass


from time import sleep
from ovos_utils.messagebus import get_mycroft_bus


bus = get_mycroft_bus("192.168.1.70")

boat = MovingHeart(bus=bus)

for faceplate in boat:
    faceplate.display()
    sleep(0.5)