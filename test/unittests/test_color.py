import unittest
from ovos_utils.colors import Color, ColorOutOfSpace


class TestColorHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.red = Color.from_name("red")
        cls.green = Color.from_name("green")
        cls.light_blue = Color.from_name("light blue")
        cls.white = Color.from_name("whitee")
        cls.undefined_color = ColorOutOfSpace()
        cls.unnamed_color = Color.from_rgb(120, 224, 4)
        cls.artificial_color = Color.from_name("black swamp green")
        cls.constructed = ColorOutOfSpace()
        cls.constructed.set_blue(0.4)
        cls.constructed.set_green(0.1)
        cls.constructed.set_luminance(0.15)

    def test_color_formats(self):
        self.assertEqual(self.white.hex, "#fff")
        self.assertEqual(self.red.hex, "#f00")

        self.assertEqual(self.white.rgb255, (255, 255, 255))
        self.assertEqual(self.red.rgb255, (255, 0, 0))

        self.assertEqual(self.red.hsv, (0.0, 1.0, 1.0))
        self.assertEqual(self.white.hsv, (0.0, 0.0, 1.0))

        self.assertEqual(self.red.hls, (0.0, 0.5, 1.0))
        self.assertEqual(self.white.hls, (0.0, 1.0, 0.0))

    def test_constructors(self):
        self.assertEqual(self.white, Color("white"))
        self.assertEqual(self.white, Color.from_rgb(255, 255, 255))
        self.assertEqual(self.white, Color.from_rgb_percent(1, 1, 1))
        self.assertEqual(self.white, Color.from_hex("#fff"))
        # TODO FIXME
        #self.assertEqual(self.white, Color.from_hsv(0.0, 0.0, 1.0))
        #self.assertEqual(self.white, Color.from_hls(0.0, 1.0, 0.0))

    def test_color_properties(self):
        self.assertEqual(self.red.name, "red")
        self.assertEqual(self.red.color_description, "red")
        self.assertEqual(self.light_blue.color_description, "light blue")

        self.assertEqual(self.unnamed_color.name, None)
        self.assertEqual(self.unnamed_color.color_description,
                         "yellow-ish intense orange color")
        self.assertEqual(self.unnamed_color.main_color, Color("orange"))

        self.assertEqual(self.artificial_color.hue, 0.33)
        self.assertEqual(self.artificial_color.main_color, Color("gray"))
        self.assertEqual(self.artificial_color.name, self.artificial_color.hex)
        self.assertEqual(self.artificial_color.color_description,
                         "dark red-ish black-ish gray color")

        self.assertEqual(self.constructed.main_color, Color("black"))
        self.assertEqual(self.constructed.color_description,
                         "dark blue-ish black-ish intense black color")
        self.assertEqual(self.constructed.name, self.constructed.hex)

    def test_undefined_color(self):
        empty_color = ColorOutOfSpace()
        self.assertEqual(empty_color.name, empty_color.hex)
        self.assertEqual(empty_color.hex, "#000")
        self.assertEqual(empty_color.rgb255, (0, 0, 0))
        self.assertEqual(empty_color.color_description, "black")
        self.assertEqual(empty_color.main_color, Color("gray"))


