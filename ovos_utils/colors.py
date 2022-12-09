from colorsys import rgb_to_yiq, yiq_to_rgb, rgb_to_hls, hls_to_rgb, \
    rgb_to_hsv, hsv_to_rgb
from webcolors import name_to_rgb, rgb_to_hex, rgb_to_name, \
    hex_to_name, hex_to_rgb

# TODO - lang support, we should translate names https://github.com/ubernostrum/webcolors/blob/trunk/src/webcolors/constants.py
# does this belong in LF ?


def name_to_hsv(name):
    name = name.replace(" ", "")  # see link above, requires exact matches
    r, g, b = name_to_rgb(name)
    return rgb_to_hsv(r, g, b)


def hsv_to_name(h, s, v):
    rgb = hsv_to_rgb(h, s, v)
    return rgb_to_name(rgb)


def hex_to_hsv(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = rgb_to_hsv(r, g, b)
    return h, s, v


class Color:
    def __init__(self, r=255, g=255, b=255):
        self._r = r
        self._g = g
        self._b = b

    @staticmethod
    def from_name(name):
        name = name.replace(" ", "")  # see link on top of file, requires exact matches
        return Color(*name_to_rgb(name))

    @staticmethod
    def from_hls(h, l, s):
        return Color(*hls_to_rgb(h, l, s))

    @staticmethod
    def from_yiq(y, i, q):
        return Color(*yiq_to_rgb(y, i, q))

    @staticmethod
    def from_rgb(r, g, b):
        return Color(r, g, b)

    @staticmethod
    def from_hsv(h, s, v):
        return Color(*hsv_to_rgb(h, s, v))

    @staticmethod
    def from_hex(hexcode):
        return Color(*hex_to_rgb(hexcode))

    @property
    def rgb(self):
        return (int(self._r), int(self._g), int(self._b))

    @property
    def yiq(self):
        return rgb_to_yiq(*self.rgb)

    @property
    def hls(self):
        return rgb_to_hls(*self.rgb)

    @property
    def hsv(self):
        return rgb_to_hsv(*self.rgb)

    @property
    def name(self):
        try:
            return rgb_to_name(self.rgb)
        except:
            return "unnamed color"

    @property
    def hex(self):
        return rgb_to_hex(self.rgb)

    def __repr__(self):
        return "{name}:{rgb}".format(name=self.name, rgb=self.rgb)

    @property
    def as_dict(self):
        return {
            "name": self.name,
            "rgb": self.rgb,
            "hsv": self.hsv,
            "hex": self.hex,
            "hls": self.hls,
            "yiq": self.yiq
        }


if __name__ == "__main__":
    hex_color = "#ff0000"
    color_name = hex_to_name(hex_color)
    print(color_name)
    h, s, v = name_to_hsv(color_name)
    print(h, s, v)
    r, g, b = hex_to_rgb(hex_color)
    print(r, g, b)
    h, s, v = rgb_to_hsv(r, g, b)
    print(h, s, v)

    color = Color()
    print(color.name)
    print(color.as_dict)
    color = Color.from_name("red")
    print(color.name, color.rgb)
    color = Color.from_name("dark red")
    print(color.name, color.rgb)
    color = Color.from_name("darkred")
    print(color.name, color.rgb)
    print(color.as_dict)
    color = Color.from_name("violet")
    print(color.name, color.rgb)

    # color = Color()
    print(color.as_dict)
