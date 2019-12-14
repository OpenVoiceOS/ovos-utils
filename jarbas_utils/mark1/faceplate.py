from jarbas_utils.messagebus import get_mycroft_bus, Message
import collections


class FaceplateGrid(collections.MutableSequence):
    encoded = None
    repr = None
    width = 32
    height = 8

    def __init__(self, grid=None, bus=None):
        self.bus = bus
        if self.encoded:
            self.grid = self.decode(self.encoded).grid
        elif self.repr:
            self.grid = FaceplateGrid.from_string(self.repr).grid
        else:
            self.grid = grid or [[0] * self.width] * self.height

    def display(self, invert=True, clear=True):
        if self.bus is None:
            self.bus = get_mycroft_bus()
        data = {"img_code": self.encode(invert),
                "clearPrev": clear}
        self.bus.emit(Message('enclosure.mouth.display', data))

    def print(self):
        print(self.to_string())

    def encode(self, invert=True):
        # to understand how this function works you need to understand how the
        # Mark I arduino proprietary encoding works to display to the faceplate

        # https://mycroft-ai.gitbook.io/docs/skill-development/displaying-information/mark-1-display

        # Each char value represents a width number starting with B=1
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
        # Code to let the Makrk I arduino know where to place the
        # pixels on the faceplate
        pixel_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                       'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        for binary_values in binary_list:
            number = int(binary_values, 2)
            pixel_code = pixel_codes[number]
            encode += pixel_code
        return encode

    @staticmethod
    def decode(encoded, invert=True, pad=True):
        codes = list(encoded)

        # Each char value represents a width number starting with B=1
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
            if width < FaceplateGrid.width:
                n = int((FaceplateGrid.width - width) / 2)
                if invert:
                    padding = [1] * n
                else:
                    padding = [0] * n
                for idx, row in enumerate(grid):
                    grid[idx] = padding + row + padding
        return FaceplateGrid(grid)

    @staticmethod
    def from_string(repr):
        rows = [r for r in repr.split("\n") if len(r)]
        grid = []
        for r in rows:
            row = []
            for char in list(r):
                if char == " ":
                    row.append(1)
                else:
                    row.append(0)
            while len(row) < FaceplateGrid.width:
                row.append(1)
            grid.append(row)

        return FaceplateGrid(grid)

    def to_string(self):
        repr = ""
        for row in self.grid:
            line = ""
            for col in row:
                if col:
                    line += " "
                else:
                    line += "X"
            repr += line + "\n"
        return repr

    def invert(self):
        inverted_str = self.to_string() \
            .replace("X", "_") \
            .replace(" ", "X") \
            .replace("_", " ")
        self.grid = self.from_string(inverted_str).grid
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
    repr = """
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
    repr = """ 
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

    StormIcon().invert().print()
    StormIcon().print()

    repr = """
XXXXXXXXXXX
XXXX   XXXX
XXXX   XXXX
X         X
X         X 
XXXX   XXXX
XXXX   XXXX
XXXXXXXXXXX
"""

    faceplate = FaceplateGrid.from_string(repr)

    encoded = faceplate.encode()
    print(encoded)

    decoded = faceplate.decode(encoded)
    print(decoded.encode())
    decoded.print()

    music = MusicIcon()
    print(music.encode())
    music.print()

    music.invert()
    print(music.encode())
    music.print()

