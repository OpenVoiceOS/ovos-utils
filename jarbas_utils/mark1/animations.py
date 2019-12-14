from jarbas_utils.mark1 import FacePlateAnimation, GoL


class SpaceInvader(GoL):
    str_grid = """
XXXXXXXXXXXX  XXX  XXXXXXXXXXXXX
XXXXXXXXXX X X X X X XXXXXXXXXXX
XXXXXXXX   XX  X  XX   XXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXX  XXX  XXXXXXXXXXXXX
XXXXXXXXXXXX XXXXX XXXXXXXXXXXXX
XXXXXXXXXXXX XXXXX XXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""


if __name__ == "__main__":

    game_of_life = SpaceInvader()

    for grid in game_of_life:
        grid.print()


