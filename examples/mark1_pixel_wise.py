from ovos_utils.enclosure.mark1.faceplate.icons import FaceplateGrid
from ovos_utils.messagebus import get_mycroft_bus
from time import sleep


bus = get_mycroft_bus("192.168.1.70")


grid = FaceplateGrid(bus=bus)

# grid is white
grid.display()
sleep(2)

# grid is black
grid.invert()
grid.display()
sleep(2)

# read pixels
n_pixels = len(grid)
assert grid.height == 8
assert grid.width == 32
assert grid[1][1] == 1  # 1 == black / pixel off

try:
    grid[grid.height]
except IndexError:
    pass # 0 <= i < grid.height
try:
    grid[grid.height-1][grid.width]
except IndexError:
    pass # 0 <= j < grid.width

# create a dotted line
grid[4][0] = 0 # white
grid[4][5] = 0 # white
grid[4][10] = 0 # white
grid[4][15] = 0 # white
grid[4][20] = 0 # white
grid[4][25] = 0 # white
grid[4][30] = 0 # white
grid.display()

# optionally disable invert
# if 1 == white / pixel on
# makes more sense to you
sleep(2)
grid.display(invert=False)

