from jarbas_utils.messagebus import get_mycroft_bus, Message
import collections


class FaceplateGrid(collections.MutableSequence):
    encoded = None
    str_grid = None
    pad_char = "."

    def __init__(self, grid=None, bus=None):
        self.bus = bus
        if self.encoded:
            self.grid = self.decode(self.encoded).grid
        elif self.str_grid:
            self.grid = FaceplateGrid.from_string(self.str_grid).grid
        else:
            self.grid = grid or [[0] * 32] * 8  # full size is 32*8

    @property
    def height(self):
        return len(self.grid)

    @property
    def width(self):
        return max([len(r) for r in self.grid])

    def display(self, invert=True, clear=True):
        # TODO handle x, y start position
        if self.bus is None:
            self.bus = get_mycroft_bus()
        data = {"img_code": self.encode(invert),
                "clearPrev": clear}
        self.bus.emit(Message('enclosure.mouth.display', data))

    def print(self, draw_padding=True):
        print(self.to_string(draw_padding=draw_padding))

    def encode(self, invert=False):
        # to understand how this function works you need to understand how the
        # Mark I arduino proprietary encoding works to display to the faceplate

        # https://mycroft-ai.gitbook.io/docs/skill-development/displaying-information/mark-1-display

        # Each char value str_gridesents a width number starting with B=1
        # then increment 1 for the next. ie C=2
        width_codes = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                       'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
                       'X', 'Y', 'Z', '[', '\\', ']', '^', '_', '`', 'a']

        height_codes = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

        encode = width_codes[self.width - 1]
        encode += height_codes[self.height - 1]

        # Turn the image pixels into binary values 1's and 0's
        # the Mark I face plate encoding uses binary values to
        # binary_values returns a list of 1's and 0s'. ie ['1', '1', '0', ...]
        binary_values = []
        for i in range(self.width):  # pixels
            for j in range(self.height):  # lines
                pixels = self.grid[j]

                if pixels[i] is None:  # padding
                    pixels[i] = 0

                if pixels[i] != 0:
                    if invert is False:
                        binary_values.append('1')
                    else:
                        binary_values.append('0')
                else:
                    if invert is False:
                        binary_values.append('0')
                    else:
                        binary_values.append('1')
        # these values are used to determine how binary values
        # needs to be grouped together
        number_of_bottom_pixel = 0

        if self.height > 4:
            number_of_top_pixel = 4
            number_of_bottom_pixel = self.height - 4
        else:
            number_of_top_pixel = self.height

        # this loop will group together the individual binary values
        # ie. binary_list = ['1111', '001', '0101', '100']
        binary_list = []
        binary_code = ''
        increment = 0
        alternate = False
        for val in binary_values:
            binary_code += val
            increment += 1
            if increment == number_of_top_pixel and alternate is False:
                # binary code is reversed for encoding
                binary_list.append(binary_code[::-1])
                increment = 0
                binary_code = ''
                alternate = True
            elif increment == number_of_bottom_pixel and alternate is True:
                binary_list.append(binary_code[::-1])
                increment = 0
                binary_code = ''
                alternate = False
        # Code to let the Mark I arduino know where to place the
        # pixels on the faceplate
        pixel_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                       'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        for binary_values in binary_list:
            number = int(binary_values, 2)
            pixel_code = pixel_codes[number]
            encode += pixel_code
        return encode

    @staticmethod
    def decode(encoded, invert=False, pad=False):
        codes = list(encoded)

        # Each char value str_gridesents a width number starting with B=1
        # then increment 1 for the next. ie C=2
        width_codes = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                       'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
                       'X', 'Y', 'Z', '[', '\\', ']', '^', '_', '`', 'a']

        height_codes = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

        height = height_codes.index(codes[1]) + 1
        width = width_codes.index(codes[0]) + 1

        # Code to let the Mark I arduino know where to place the
        # pixels on the faceplate
        pixel_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                       'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        codes.reverse()
        binary_list = []
        for pixel_code in codes[:-2]:
            number = pixel_codes.index(pixel_code.upper())
            bin_str = str(bin(number))[2:]
            while not len(bin_str) == 4:
                bin_str = "0" + bin_str
            binary_list += [bin_str]

        binary_list.reverse()

        for idx, binary_code in enumerate(binary_list):
            # binary code is reversed for encoding
            binary_list[idx] = binary_code[::-1]

        binary_code = "".join(binary_list)

        # Turn the image pixels into binary values 1's and 0's
        # the Mark I face plate encoding uses binary values to
        # binary_values returns a list of 1's and 0s'. ie ['1', '1', '0', ...]
        grid = []
        # binary_code is a sequence of column by column
        cols = [list(binary_code)[x:x + height] for x in range(0, len(list(binary_code)), height)]

        for x in range(height):
            row = []
            for y in range(width):
                bit = int(cols[y][x])
                if invert:
                    if bit:
                        bit = 0
                    else:
                        bit = 1
                row.append(bit)
            grid.append(row)

        #  handle padding
        if pad:
            if width < 32:
                n = int((32 - width) / 2)
                if invert:
                    padding = [1] * n
                else:
                    padding = [0] * n
                for idx, row in enumerate(grid):
                    grid[idx] = padding + row + padding
            if height < 8:
                pass # TODO vertical padding
        return FaceplateGrid(grid)

    def from_string(self, str_grid):
        rows = [r for r in str_grid.split("\n") if len(r)]
        grid = []
        for r in rows:
            row = []
            for char in list(r):
                if char == " ":
                    row.append(1)
                elif char == FaceplateGrid.pad_char:
                    row.append(None)
                else:
                    row.append(0)
            while len(row) < self.width:
                row.append(None)
            grid.append(row)
        self.grid = grid
        return self

    def to_string(self, draw_padding=False):
        str_grid = ""
        for row in self.grid:
            line = ""
            for col in row:
                if col is None and draw_padding:
                    line += self.pad_char
                elif col == 1:
                    line += " "
                elif col == 0:
                    line += "X"
            str_grid += line + "\n"
        return str_grid

    def invert(self):
        for x in range(self.height):
            for y in range(self.width):
                if self.grid[x][y] == 0:
                    self.grid[x][y] = 1
                elif self.grid[x][y] == 1:
                    self.grid[x][y] = 0
        return self

    def __len__(self):
        # number of pixels
        return self.width * self.height

    def __delitem__(self, index):
        self.grid.__delitem__(index)

    def insert(self, index, value):
        self.grid.insert(index - 1, value)

    def __setitem__(self, index, value):
        self.grid.__setitem__(index, value)

    def __getitem__(self, index):
        return self.grid.__getitem__(index)


class MusicIcon(FaceplateGrid):
    str_grid = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXX     XXXXXXXXXXXXX
XXXXXXXXXXXXXX     XXXXXXXXXXXXX
XXXXXXXXXXXXXX XXX XXXXXXXXXXXXX
XXXXXXXXXXXXXX XXX XXXXXXXXXXXXX
XXXXXXXXXXXXX  XX  XXXXXXXXXXXXX
XXXXXXXXXXXX   X   XXXXXXXXXXXXX
XXXXXXXXXXXXX XXX XXXXXXXXXXXXXX
"""

    def __init__(self):
        super().__init__()
        self.invert()


class PlusIcon(FaceplateGrid):
    str_grid = """ 
              xxx    
              xxx    
           xxxxxxxxx 
           xxxxxxxxx 
              xxx    
              xxx    

"""


# Default weather icons for mark1
class SunnyIcon(FaceplateGrid):
    encoded = "IICEIBMDNLMDIBCEAA"


class PartlyCloudyIcon(FaceplateGrid):
    encoded = "IIEEGBGDHLHDHBGEEA"


class CloudyIcon(FaceplateGrid):
    encoded = "IIIBMDMDODODODMDIB"


class LightRainIcon(FaceplateGrid):
    encoded = "IIMAOJOFPBPJPFOBMA"


class RainIcon(FaceplateGrid):
    encoded = "IIMIOFOBPFPDPJOFMA"


class StormIcon(FaceplateGrid):
    encoded = "IIAAIIMEODLBJAAAAA"


class SnowIcon(FaceplateGrid):
    encoded = "IIJEKCMBPHMBKCJEAA"


class WindIcon(FaceplateGrid):
    encoded = "IIABIBIBIJIJJGJAGA"


if __name__ == "__main__":

    #StormIcon().invert().print()
    #StormIcon().print()

    str_grid = """
XXXXXXXXXXX
XXXX   XXXX
XXXX   XXXX
X         X
X         X
XXXX   XXXX
XXXX   XXXX
XXXXXXXXXXX
"""

    faceplate = FaceplateGrid().from_string(str_grid)
    faceplate.print()  # notice padding with . . .

    encoded = faceplate.encode()   # padding replaced with "off"

    print(encoded)

    decoded = faceplate.decode(encoded)
    assert decoded.encode() == encoded
    decoded.invert()

    decoded.print()



    exit()
    music = MusicIcon()
    print(music.encode())
    music.print()

    music.invert()
    print(music.encode())
    music.print()

