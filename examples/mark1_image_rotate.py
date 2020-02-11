from jarbas_utils.mark1.icons import Boat, MusicIcon, StormIcon, SnowIcon, \
    SunnyIcon, PartlyCloudyIcon, PlusIcon
from jarbas_utils.messagebus import get_mycroft_bus
from time import sleep


bus = get_mycroft_bus("192.168.1.70")


images = [Boat(bus=bus),
          MusicIcon(bus=bus).invert(),
          StormIcon(bus=bus),
          SunnyIcon(bus=bus),
          PartlyCloudyIcon(bus=bus),
          PlusIcon(bus=bus).invert(),
          SnowIcon(bus=bus)]

for faceplate in images:
    faceplate.display(invert=False)
    sleep(3)