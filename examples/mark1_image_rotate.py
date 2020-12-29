from ovos_utils.enclosure.mark1.faceplate.icons import Boat, MusicIcon, StormIcon, \
    SnowIcon, SunnyIcon, PartlyCloudyIcon, PlusIcon, SkullIcon, CrossIcon, \
    HollowHeartIcon, HeartIcon, DeadFishIcon, InfoIcon, \
    ArrowLeftIcon, JarbasAI, WarningIcon
from ovos_utils.messagebus import get_mycroft_bus
from time import sleep

bus = get_mycroft_bus("192.168.1.70")

images = [Boat(bus=bus),
          MusicIcon(bus=bus),
          StormIcon(bus=bus),
          SunnyIcon(bus=bus),
          PartlyCloudyIcon(bus=bus),
          PlusIcon(bus=bus),
          CrossIcon(bus=bus),
          SnowIcon(bus=bus),
          SkullIcon(bus=bus),
          HeartIcon(bus=bus),
          HollowHeartIcon(bus=bus),
          ArrowLeftIcon(bus=bus),
          JarbasAI(bus=bus),
          WarningIcon(bus=bus),
          InfoIcon(bus=bus),
          DeadFishIcon(bus=bus)]

from ovos_utils.enclosure.mark1.faceplate.icons import SpaceInvader1, \
    SpaceInvader2, SpaceInvader3, SpaceInvader4
images = [SpaceInvader1(bus=bus),
          SpaceInvader2(bus=bus),
          SpaceInvader3(bus=bus),
          SpaceInvader4(bus=bus)]
for faceplate in images:
    faceplate.print()
    faceplate.display()
    sleep(3)
