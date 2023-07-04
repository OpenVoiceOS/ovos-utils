from ovos_utils.messagebus import FakeMessage as Message, dig_for_message


class EnclosureAPI:
    """
    This API is intended to be used to interface with the hardware
    that is running Mycroft.  It exposes all possible commands which
    can be sent to a Mycroft enclosure implementation.

    Different enclosure implementations may implement this differently
    and/or may ignore certain API calls completely.  For example,
    the eyes_color() API might be ignore on a Mycroft that uses simple
    LEDs which only turn on/off, or not at all on an implementation
    where there is no face at all.
    """

    def __init__(self, bus=None, skill_id=""):
        self.bus = bus
        self.skill_id = skill_id

    def set_bus(self, bus):
        self.bus = bus

    def set_id(self, skill_id):
        self.skill_id = skill_id

    def _get_source_message(self):
        return dig_for_message() or \
            Message("", context={"destination": ["enclosure"],
                                 "skill_id": self.skill_id})

    def register(self, skill_id=""):
        """Registers a skill as active. Used for speak() and speak_dialog()
        to 'patch' a previous implementation. Somewhat hacky.
        DEPRECATED - unused
        """
        source_message = self._get_source_message()
        skill_id = skill_id or self.skill_id
        self.bus.emit(source_message.forward("enclosure.active_skill",
                                             {"skill_id": skill_id}))

    def reset(self):
        """The enclosure should restore itself to a started state.
        Typically this would be represented by the eyes being 'open'
        and the mouth reset to its default (smile or blank).
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.reset"))

    def system_reset(self):
        """The enclosure hardware should reset any CPUs, etc."""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.system.reset"))

    def system_mute(self):
        """Mute (turn off) the system speaker."""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.system.mute"))

    def system_unmute(self):
        """Unmute (turn on) the system speaker."""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.system.unmute"))

    def system_blink(self, times):
        """The 'eyes' should blink the given number of times.
        Args:
            times (int): number of times to blink
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.system.blink",
                                             {'times': times}))

    def eyes_on(self):
        """Illuminate or show the eyes."""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.on"))

    def eyes_off(self):
        """Turn off or hide the eyes."""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.off"))

    def eyes_blink(self, side):
        """Make the eyes blink
        Args:
            side (str): 'r', 'l', or 'b' for 'right', 'left' or 'both'
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.blink",
                                             {'side': side}))

    def eyes_narrow(self):
        """Make the eyes look narrow, like a squint"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.narrow"))

    def eyes_look(self, side):
        """Make the eyes look to the given side
        Args:
            side (str): 'r' for right
                        'l' for left
                        'u' for up
                        'd' for down
                        'c' for crossed
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.look",
                                             {'side': side}))

    def eyes_color(self, r=255, g=255, b=255):
        """Change the eye color to the given RGB color
        Args:
            r (int): 0-255, red value
            g (int): 0-255, green value
            b (int): 0-255, blue value
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.color",
                                             {'r': r, 'g': g, 'b': b}))

    def eyes_setpixel(self, idx, r=255, g=255, b=255):
        """Set individual pixels of the Mark 1 neopixel eyes
        Args:
            idx (int): 0-11 for the right eye, 12-23 for the left
            r (int): The red value to apply
            g (int): The green value to apply
            b (int): The blue value to apply
        """
        source_message = self._get_source_message()
        if idx < 0 or idx > 23:
            raise ValueError(f'idx ({idx}) must be between 0-23')
        self.bus.emit(source_message.forward("enclosure.eyes.setpixel",
                                             {'idx': idx,
                                              'r': r, 'g': g, 'b': b}))

    def eyes_fill(self, percentage):
        """Use the eyes as a type of progress meter
        Args:
            percentage (int): 0-49 fills the right eye, 50-100 also covers left
        """
        source_message = self._get_source_message()
        if percentage < 0 or percentage > 100:
            raise ValueError(f'percentage ({percentage}) must be between 0-100')
        self.bus.emit(source_message.forward("enclosure.eyes.fill",
                                             {'percentage': percentage}))

    def eyes_brightness(self, level=30):
        """Set the brightness of the eyes in the display.
        Args:
            level (int): 1-30, bigger numbers being brighter
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.level",
                                             {'level': level}))

    def eyes_reset(self):
        """Restore the eyes to their default (ready) state."""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.reset"))

    def eyes_spin(self):
        """Make the eyes 'roll'
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.spin"))

    def eyes_timed_spin(self, length):
        """Make the eyes 'roll' for the given time.
        Args:
            length (int): duration in milliseconds of roll, None = forever
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.eyes.timedspin",
                                             {'length': length}))

    def eyes_volume(self, volume):
        """Indicate the volume using the eyes
        Args:
            volume (int): 0 to 11
        """
        source_message = self._get_source_message()
        if volume < 0 or volume > 11:
            raise ValueError('volume ({}) must be between 0-11'.
                             format(str(volume)))
        self.bus.emit(source_message.forward("enclosure.eyes.volume",
                                             {'volume': volume}))

    def mouth_reset(self):
        """Restore the mouth display to normal (blank)"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.reset"))

    def mouth_talk(self):
        """Show a generic 'talking' animation for non-synched speech"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.talk"))

    def mouth_think(self):
        """Show a 'thinking' image or animation"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.think"))

    def mouth_listen(self):
        """Show a 'thinking' image or animation"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.listen"))

    def mouth_smile(self):
        """Show a 'smile' image or animation"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.smile"))

    def mouth_viseme(self, start, viseme_pairs):
        """ Send mouth visemes as a list in a single message.

            Args:
                start (int):    Timestamp for start of speech
                viseme_pairs:   Pairs of viseme id and cumulative end times
                                (code, end time)

                                codes:
                                 0 = shape for sounds like 'y' or 'aa'
                                 1 = shape for sounds like 'aw'
                                 2 = shape for sounds like 'uh' or 'r'
                                 3 = shape for sounds like 'th' or 'sh'
                                 4 = neutral shape for no sound
                                 5 = shape for sounds like 'f' or 'v'
                                 6 = shape for sounds like 'oy' or 'ao'
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.viseme_list",
                                             {"start": start,
                                              "visemes": viseme_pairs}))

    def mouth_text(self, text=""):
        """Display text (scrolling as needed)
        Args:
            text (str): text string to display
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.text",
                                             {'text': text}))

    def mouth_display(self, img_code="", x=0, y=0, refresh=True):
        """Display images on faceplate. Currently supports images up to 16x8,
           or half the face. You can use the 'x' parameter to cover the other
           half of the faceplate.
        Args:
            img_code (str): text string that encodes a black and white image
            x (int): x offset for image
            y (int): y offset for image
            refresh (bool): specify whether to clear the faceplate before
                            displaying the new image or not.
                            Useful if you'd like to display multiple images
                            on the faceplate at once.
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward('enclosure.mouth.display',
                                             {'img_code': img_code,
                                              'xOffset': x,
                                              'yOffset': y,
                                              'clearPrev': refresh}))

    def mouth_display_png(self, image_absolute_path,
                          invert=False, x=0, y=0, refresh=True):
        """ Send an image to the enclosure.

        Args:
            image_absolute_path (string): The absolute path of the image
            invert (bool): inverts the image being drawn.
            x (int): x offset for image
            y (int): y offset for image
            refresh (bool): specify whether to clear the faceplate before
                            displaying the new image or not.
                            Useful if you'd like to display muliple images
                            on the faceplate at once.
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.mouth.display_image",
                                             {'img_path': image_absolute_path,
                                              'xOffset': x,
                                              'yOffset': y,
                                              'invert': invert,
                                              'clearPrev': refresh}))

    def weather_display(self, img_code, temp):
        """Show a the temperature and a weather icon

        Args:
            img_code (char): one of the following icon codes
                         0 = sunny
                         1 = partly cloudy
                         2 = cloudy
                         3 = light rain
                         4 = raining
                         5 = stormy
                         6 = snowing
                         7 = wind/mist
            temp (int): the temperature (either C or F, not indicated)
        """
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward("enclosure.weather.display",
                                             {'img_code': img_code,
                                              'temp': temp}))

    def activate_mouth_events(self):
        """Enable movement of the mouth with speech"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward('enclosure.mouth.events.activate'))

    def deactivate_mouth_events(self):
        """Disable movement of the mouth with speech"""
        source_message = self._get_source_message()
        self.bus.emit(source_message.forward(
            'enclosure.mouth.events.deactivate'))

    def get_eyes_color(self):
        """Get the eye RGB color for all pixels
        Returns:
           (list) pixels - list of (r,g,b) tuples for each eye pixel
        """
        source_message = self._get_source_message()
        message = source_message.forward("enclosure.eyes.rgb.get")
        response = self.bus.wait_for_response(message, "enclosure.eyes.rgb")
        if response:
            return response.data["pixels"]
        raise TimeoutError("Enclosure took too long to respond")

    def get_eyes_pixel_color(self, idx):
        """Get the RGB color for a specific eye pixel
        Returns:
            (r,g,b) tuples for selected pixel
        """
        if idx < 0 or idx > 23:
            raise ValueError(f'idx ({idx}) must be between 0-23')
        return self.get_eyes_color()[idx]
