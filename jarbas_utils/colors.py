from colorsys import rgb_to_yiq, rgb_to_hls, yiq_to_rgb, hls_to_rgb, rgb_to_hsv, hsv_to_rgb
from colour import Color as _Color
from jarbas_utils.log import LOG


class UnrecognizedColorName(ValueError):
    """ No color defined with this name """


class Color(_Color):

    @property
    def name(self):
        if self.web != self.hex_l:
            return self.web
        LOG.warning("This color is not officially named, use self.color_description")
        return None

    @staticmethod
    def from_name(name):
        try:
            name = name.lower().replace(" ", "").strip()
            return Color(name)
        except:
            # try to parse color description
            color = ColorOutOfSpace()

            if "bright" in name:
                color.set_luminance(0.7)
            if "dark" in name:
                color.set_luminance(0.3)

            if "light" in name:
                color.set_saturation(0.4)
            if "grey" in name or "gray" in name:
                color.set_saturation(0.25)

            if "black" in name:
                color.set_luminance(0.1)
            if "white" in name:
                color.set_luminance(1)

            red = 0.0
            orange = 0.10
            yellow = 0.16
            green = 0.33
            cyan = 0.5
            blue = 0.66
            violet = 0.83

            if "orange" in name:
                color.hue = orange
            elif "yellow" in name:
                color.hue = yellow
            elif "green" in name:
                color.hue = green
            elif "cyan" in name:
                color.hue = cyan
            elif "blue" in name:
                color.hue = blue
            elif "violet" in name:
                color.hue = violet
            else:
                color.hue = red

            return color

    @property
    def color_description(self):
        if self.web != self.hex:
            return self.web
        name = ""
        # light vs dark
        if self.luminance <= 0.3:
            name += "dark "
        elif self.luminance >= 0.6:
            name += "bright "

        # hue
        # R >== B >= G Red
        if self.red >= self.blue >= self.green:
            name += "red-ish "
        # R >== G >= = B 	Orange
        elif self.red >= self.green >= self.blue:
            name += "orange-ish "
        # G >= R >== B Yellow
        elif self.green >= self.red >= self.blue:
            name += "yellow-ish "
        # G >== B >= R  Green
        elif self.green >= self.blue >= self.red:
            name += "green-ish "
        # B >= G >= R  Blue
        elif self.blue >= self.green >= self.red:
            name += "blue-ish "
        # B >= R >== G  Violet
        elif self.blue >= self.red >= self.green:
            name += "purple-ish "

        # luminance
        if self.luminance <= 0.15:
            name += "black-ish "
        elif self.luminance >= 0.85:
            name += "white-ish "

        # saturation
        if self.saturation >= 0.85:
            name += "intense "
        if self.saturation <= 0.3:
            name += "grey "
        else:
            thresh = 0.5

            orange = 0.10
            yellow = 0.16
            green = 0.33
            cyan = 0.5
            blue = 0.66
            violet = 0.83

            if orange - thresh <= self.hue <= orange + thresh:
                name += "orange "
            elif yellow - thresh <= self.hue <= yellow + thresh:
                name += "yellow "
            elif green - thresh <= self.hue <= green + thresh:
                name += "green "
            elif cyan - thresh <= self.hue <= cyan + thresh:
                name += "cyan "
            elif blue - thresh <= self.hue <= blue + thresh:
                name += "blue "
            elif violet - thresh <= self.hue <= violet + thresh:
                name += "violet "
            else:
                name += "red "
        name += "color"

        return name

    #### HEX ####
    @staticmethod
    def from_hex(hex_value):
        return Color(hex_value)

    #### RGB ####
    @property
    def rgb255(self):
        return (int(self.red * 256),
                int(self.green * 256),
                int(self.blue * 256))

    def rgb_percent(self):
        return self.rgb

    @staticmethod
    def from_rgb(r, g, b):
        return Color(rgb=(r/255, g/255, b/255))

    @staticmethod
    def from_rgb_percent(r, g, b):
        if isinstance(r, str) or isinstance(g, str) or isinstance(b, str):
            r = float(r.replace("%", ""))
            g = float(g.replace("%", ""))
            b = float(b.replace("%", ""))
        return Color(rgb=(r, g, b))

    #### HSV ####
    @staticmethod
    def from_hsv(h, s, v):
        r, g, b = hsv_to_rgb(h, s, v)
        return Color.from_rgb(r, g, b)

    @property
    def hsv(self):
        return rgb_to_hsv(self.red, self.green, self.blue)

    #### HLS ####
    @staticmethod
    def from_hls(h, l, s):
        r, g, b = hls_to_rgb(h, l, s)
        return Color.from_rgb(r, g, b)

    @property
    def hls(self):
        return rgb_to_hls(self.red, self.green, self.blue)

    #### YIQ ####
    @staticmethod
    def from_yiq(y, i, q):
        r, g, b = yiq_to_rgb(y, i, q)
        return Color.from_rgb(r, g, b)

    @property
    def yiq(self):
        return rgb_to_yiq(self.red, self.green, self.blue)

    def __str__(self):
        return self.hex_l


class ColorOutOfSpace(Color):
    @property
    def name(self):
        # H.P. Lovecraft - https://www.youtube.com/watch?v=4liRxrDzS5I
        # return "The Color Out of Space"
        return self.hex


if __name__ == "__main__":
    black = Color()
    assert black == Color("black")

    white = Color.from_name("white")
    assert white == Color.from_rgb(255, 255, 255)

    color = Color.from_name("NNNNNNNNNNNNNNNNNN")
    assert isinstance(color, ColorOutOfSpace)
    assert color.name != "black"
    assert color.color_description == "black"

    color = Color.from_rgb(0, 120, 240)
    assert color.name is None
    color.set_saturation(0.3)
    color.set_luminance(0.7)
    assert color.color_description == "bright blue-ish grey color"
    assert color.rgb255 == (156, 179, 202)

    aprox_color = Color.from_name("bright blue-ish grey color")
    assert aprox_color.color_description == "bright blue-ish grey color"
    assert aprox_color.rgb255 != color.rgb255
    assert aprox_color.rgb255 == (160, 161, 198)

