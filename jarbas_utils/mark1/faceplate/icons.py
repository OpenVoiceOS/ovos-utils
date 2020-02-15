from jarbas_utils.mark1.faceplate import FaceplateGrid


# drawing in python
class BlackScreen(FaceplateGrid):
    # Basically a util class to handle
    # inverting on __init__
    str_grid = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invert()


class MusicIcon(BlackScreen):
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


class PlusIcon(FaceplateGrid):
    str_grid = """
              xxx               
              xxx               
           xxxxxxxxx            
           xxxxxxxxx            
              xxx               
              xxx               
"""


class HeartIcon(FaceplateGrid):
    str_grid = """
            xx   xx             
           xxxx xxxx            
           xxxxxxxxx            
            xxxxxxx             
             xxxxx              
              xxx               
               x                
"""


class HollowHeartIcon(FaceplateGrid):
    str_grid = """
            xx   xx             
           x  x x  x            
           x   x   x            
            x     x             
             x   x              
               x                
"""


class SkullIcon(FaceplateGrid):
    str_grid = """
            xxxxxxx             
           x  xxx  x            
           xxxxxxxxx            
            xxx xxx             
             xxxxx              
             x x x              
"""


class DeadFishIcon(FaceplateGrid):
    str_grid = """
                                
   x            xxxx            
    x  x x x   xx xxx           
     xxxxxxxxxxxxxxxxx          
    x  x x x   xxxxxx            
   x            xxxx            
"""


class InfoIcon(BlackScreen):
    str_grid = """
XXXXXXXXXXXXXXX   XXXXXXXXXXXXXX
XXXXXXXXXXXXXXX   XXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXX    XXXXXXXXXXXXXX
XXXXXXXXXXXXXXX   XXXXXXXXXXXXXX
XXXXXXXXXXXXXXX   XXXXXXXXXXXXXX
XXXXXXXXXXXXXXX    XXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""


class WifiIcon(BlackScreen):
    str_grid = """
XXXXXXXXXXXX       XXXXXXXXXXXXX
XXXXXXXXXXX XXXXXXX XXXXXXXXXXXX
XXXXXXXXXX XXXXXXXXX XXXXXXXXXXX
XXXXXXXXXXXX       XXXXXXXXXXXXX
XXXXXXXXXXX XXXXXXX XXXXXXXXXXXX
XXXXXXXXXXXXXX   XXXXXXXXXXXXXXX
XXXXXXXXXXXXXX   XXXXXXXXXXXXXXX
XXXXXXXXXXXXXX   XXXXXXXXXXXXXXX
"""


class ArrowLeftIcon(BlackScreen):
    str_grid = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXX   XXXXXXXXXXXXXXXX
XXXXXXXXXXXX   XXXXXXXXXXXXXXXXX
XXXXXXXXXXX   X       XXXXXXXXXX
XXXXXXXXXX   X        XXXXXXXXXX
XXXXXXXXXXX   X       XXXXXXXXXX
XXXXXXXXXXXX   XXXXXXXXXXXXXXXXX
XXXXXXXXXXXXX   XXXXXXXXXXXXXXXX
"""


class WarningIcon(BlackScreen):
    str_grid = """
XXXXXXXXXXXXXXX XXXXXXXXXXXXXXXX
XXXXXXXXXXXXXX   XXXXXXXXXXXXXXX
XXXXXXXXXXXXX  X  XXXXXXXXXXXXXX
XXXXXXXXXXXX  XXX  XXXXXXXXXXXXX
XXXXXXXXXXX   XXX   XXXXXXXXXXXX
XXXXXXXXXXX         XXXXXXXXXXXX
XXXXXXXXXX    XXX    XXXXXXXXXXX
XXXXXXXXXX     X     XXXXXXXXXXX
"""


class CrossIcon(BlackScreen):
    str_grid = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXX XXXXX XXXXXXXXXXXX
XXXXXXXXXXXX   XXX   XXXXXXXXXXX
XXXXXXXXXXXXX   X   XXXXXXXXXXXX
XXXXXXXXXXXXXXX   XXXXXXXXXXXXXX
XXXXXXXXXXXXX   X   XXXXXXXXXXXX
XXXXXXXXXXXX   XXX   XXXXXXXXXXX
XXXXXXXXXXXXX XXXXX XXXXXXXXXXXX
"""


class JarbasAI(BlackScreen):
    str_grid = """
X   XXXXXXXXXXXXXXXXXXXXXXX   X 
XX XXXXXXXXXXXXXXXXXXXXXXXX X XX
XX XXXXXXXXXX XXXXXXXXXXXXX X X 
XX XXXXXXXXXX XXXXXXXXX   X   X 
XX XX   X X X    XX   X XXX X X 
 X X XX X  XX XX X XX X   X X X 
 X X XX X XXX XX X XX XXX X X X 
   X    X XXX    X    X   X X X 
"""


# Encoded icons
class Boat(FaceplateGrid):
    encoded = "QIAAABACAGIEMEOEPHAEAGACABABAAAAAA"


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

