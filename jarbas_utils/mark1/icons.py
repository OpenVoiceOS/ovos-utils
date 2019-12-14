from jarbas_utils.mark1 import FaceplateGrid

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

    StormIcon().invert().print()
    StormIcon().print()

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

    music = MusicIcon()
    print(music.encode())
    music.print()

    music.invert()
    music.print()

    f = FaceplateGrid().randomize().invert()
    f.print()