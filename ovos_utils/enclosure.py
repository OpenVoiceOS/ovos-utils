import time
import socket
from ovos_utils.log import LOG
from ovos_utils.messagebus import Message, get_mycroft_bus


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

    def __init__(self, bus=None):
        self.bus = bus or get_mycroft_bus()

    def reset(self):
        """The enclosure should restore itself to a started state.
        Typically this would be represented by the eyes being 'open'
        and the mouth reset to its default (smile or blank).
        """
        self.bus.emit(Message("enclosure.reset"))

    def system_reset(self):
        """The enclosure hardware should reset any CPUs, etc."""
        self.bus.emit(Message("enclosure.system.reset"))

    def system_mute(self):
        """Mute (turn off) the system speaker."""
        self.bus.emit(Message("enclosure.system.mute"))

    def system_unmute(self):
        """Unmute (turn on) the system speaker."""
        self.bus.emit(Message("enclosure.system.unmute"))

    def system_blink(self, times):
        """The 'eyes' should blink the given number of times.
        Args:
            times (int): number of times to blink
        """
        self.bus.emit(Message("enclosure.system.blink", {'times': times}))

    def eyes_on(self):
        """Illuminate or show the eyes."""
        self.bus.emit(Message("enclosure.eyes.on"))

    def eyes_off(self):
        """Turn off or hide the eyes."""
        self.bus.emit(Message("enclosure.eyes.off"))

    def eyes_blink(self, side):
        """Make the eyes blink
        Args:
            side (str): 'r', 'l', or 'b' for 'right', 'left' or 'both'
        """
        self.bus.emit(Message("enclosure.eyes.blink", {'side': side}))

    def eyes_narrow(self):
        """Make the eyes look narrow, like a squint"""
        self.bus.emit(Message("enclosure.eyes.narrow"))

    def eyes_look(self, side):
        """Make the eyes look to the given side
        Args:
            side (str): 'r' for right
                        'l' for left
                        'u' for up
                        'd' for down
                        'c' for crossed
        """
        self.bus.emit(Message("enclosure.eyes.look", {'side': side}))

    def eyes_color(self, r=255, g=255, b=255):
        """Change the eye color to the given RGB color
        Args:
            r (int): 0-255, red value
            g (int): 0-255, green value
            b (int): 0-255, blue value
        """
        self.bus.emit(Message("enclosure.eyes.color",
                              {'r': r, 'g': g, 'b': b}))

    def eyes_setpixel(self, idx, r=255, g=255, b=255):
        """Set individual pixels of the Mark 1 neopixel eyes
        Args:
            idx (int): 0-11 for the right eye, 12-23 for the left
            r (int): The red value to apply
            g (int): The green value to apply
            b (int): The blue value to apply
        """
        if idx < 0 or idx > 23:
            raise ValueError('row ({}) must be between 0-23'.format(str(idx)))
        self.bus.emit(Message("enclosure.eyes.setpixel",
                              {'row': idx, 'r': r, 'g': g, 'b': b}))

    def eyes_fill(self, percentage):
        """Use the eyes as a type of progress meter
        Args:
            amount (int): 0-49 fills the right eye, 50-100 also covers left
        """
        if percentage < 0 or percentage > 100:
            raise ValueError('percentage ({}) must be between 0-100'.
                             format(str(percentage)))
        self.bus.emit(Message("enclosure.eyes.fill",
                              {'percentage': percentage}))

    def eyes_brightness(self, level=30):
        """Set the brightness of the eyes in the display.
        Args:
            level (int): 1-30, bigger numbers being brighter
        """
        self.bus.emit(Message("enclosure.eyes.level", {'level': level}))

    def eyes_reset(self):
        """Restore the eyes to their default (ready) state."""
        self.bus.emit(Message("enclosure.eyes.reset"))

    def eyes_spin(self):
        """Make the eyes 'roll'
        """
        self.bus.emit(Message("enclosure.eyes.spin"))

    def eyes_timed_spin(self, length):
        """Make the eyes 'roll' for the given time.
        Args:
            length (int): duration in milliseconds of roll, None = forever
        """
        self.bus.emit(Message("enclosure.eyes.timedspin",
                              {'length': length}))

    def eyes_volume(self, volume):
        """Indicate the volume using the eyes
        Args:
            volume (int): 0 to 11
        """
        if volume < 0 or volume > 11:
            raise ValueError('volume ({}) must be between 0-11'.
                             format(str(volume)))
        self.bus.emit(Message("enclosure.eyes.volume", {'volume': volume}))

    def mouth_reset(self):
        """Restore the mouth display to normal (blank)"""
        self.bus.emit(Message("enclosure.mouth.reset"))

    def mouth_talk(self):
        """Show a generic 'talking' animation for non-synched speech"""
        self.bus.emit(Message("enclosure.mouth.talk"))

    def mouth_think(self):
        """Show a 'thinking' image or animation"""
        self.bus.emit(Message("enclosure.mouth.think"))

    def mouth_listen(self):
        """Show a 'thinking' image or animation"""
        self.bus.emit(Message("enclosure.mouth.listen"))

    def mouth_smile(self):
        """Show a 'smile' image or animation"""
        self.bus.emit(Message("enclosure.mouth.smile"))

    def mouth_viseme(self, start, viseme_pairs):
        """ Send mouth visemes as a list in a single message.

            Arguments:
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
        self.bus.emit(Message("enclosure.mouth.viseme_list",
                              {"start": start, "visemes": viseme_pairs}))

    def mouth_text(self, text=""):
        """Display text (scrolling as needed)
        Args:
            text (str): text string to display
        """
        self.bus.emit(Message("enclosure.mouth.text", {'text': text}))

    def mouth_display(self, img_code="", x=0, y=0, refresh=True):
        """Display images on faceplate.
        Args:
            img_code (str): text string that encodes a black and white image
            x (int): x offset for image
            y (int): y offset for image
            refresh (bool): specify whether to clear the faceplate before
                            displaying the new image or not.
                            Useful if you'd like to display multiple images
                            on the faceplate at once.
        """
        self.bus.emit(Message('enclosure.mouth.display',
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
        self.bus.emit(Message("enclosure.mouth.display_image",
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
        self.bus.emit(Message("enclosure.weather.display",
                              {'img_code': img_code, 'temp': temp}))

    def activate_mouth_events(self):
        """Enable movement of the mouth with speech"""
        self.bus.emit(Message('enclosure.mouth.events.activate'))

    def deactivate_mouth_events(self):
        """Disable movement of the mouth with speech"""
        self.bus.emit(Message('enclosure.mouth.events.deactivate'))

    def get_eyes_color(self):
        """
        Get the eye RGB color for all pixels

        :returns pixels (list) - list of (r,g,b) tuples for each eye pixel

        """
        message = Message("enclosure.eyes.rgb.get",
                          context={"source": "enclosure_api",
                                   "destination": "enclosure"})
        response = self.bus.wait_for_response(message, "enclosure.eyes.rgb")
        if response:
            return response.data["pixels"]
        raise TimeoutError("Enclosure took too long to respond")

    def get_eyes_pixel_color(self, idx):
        """
        Get the RGB color for a specific eye pixel

        :returns (r,g,b) tuples for selected pixel

        """
        if idx < 0 or idx > 23:
            raise ValueError('row ({}) must be between 0-23'.format(str(idx)))
        return self.get_eyes_color()[idx]


class EnclosureTemplate:
    """
    This base class is intended to be used to interface with the hardware
    that is running Mycroft.  It exposes all possible commands which
    can be sent to a Mycroft enclosure implementation.
    """

    def __init__(self, bus=None, name=""):
        self._mouth_events = False
        self._running = False
        self.bus = bus or get_mycroft_bus()
        self.log = LOG
        self.name = name

        self.bus.on("enclosure.reset", self.on_reset)

        # enclosure commands for Mycroft's Hardware.
        self.bus.on("enclosure.system.reset", self.on_system_reset)
        self.bus.on("enclosure.system.mute", self.on_system_mute)
        self.bus.on("enclosure.system.unmute", self.on_system_unmute)
        self.bus.on("enclosure.system.blink", self.on_system_blink)

        # enclosure commands for eyes
        self.bus.on('enclosure.eyes.on', self.on_eyes_on)
        self.bus.on('enclosure.eyes.off', self.on_eyes_off)
        self.bus.on('enclosure.eyes.blink', self.on_eyes_blink)
        self.bus.on('enclosure.eyes.narrow', self.on_eyes_narrow)
        self.bus.on('enclosure.eyes.look', self.on_eyes_look)
        self.bus.on('enclosure.eyes.color', self.on_eyes_color)
        self.bus.on('enclosure.eyes.level', self.on_eyes_brightness)
        self.bus.on('enclosure.eyes.volume', self.on_eyes_volume)
        self.bus.on('enclosure.eyes.spin', self.on_eyes_spin)
        self.bus.on('enclosure.eyes.timedspin', self.on_eyes_timed_spin)
        self.bus.on('enclosure.eyes.reset', self.on_eyes_reset)
        self.bus.on('enclosure.eyes.setpixel', self.on_eyes_set_pixel)
        self.bus.on('enclosure.eyes.fill', self.on_eyes_fill)

        # enclosure commands for mouth
        self.bus.on("enclosure.mouth.events.activate",
                    self._activate_mouth_events)
        self.bus.on("enclosure.mouth.events.deactivate",
                    self._deactivate_mouth_events)
        self.bus.on("enclosure.mouth.talk", self._on_mouth_talk)
        self.bus.on("enclosure.mouth.think", self._on_mouth_think)
        self.bus.on("enclosure.mouth.listen", self._on_mouth_listen)
        self.bus.on("enclosure.mouth.smile", self._on_mouth_smile)
        self.bus.on("enclosure.mouth.viseme", self._on_mouth_viseme)
        # mouth/matrix display
        self.bus.on("enclosure.mouth.reset", self.on_display_reset)
        self.bus.on("enclosure.mouth.text", self.on_text)
        self.bus.on("enclosure.mouth.display", self.on_display)
        self.bus.on("enclosure.weather.display", self.on_weather_display)

        # audio events
        self.bus.on('recognizer_loop:record_begin', self.on_record_begin)
        self.bus.on('recognizer_loop:record_end', self.on_record_end)
        self.bus.on("recognizer_loop:sleep", self.on_sleep)
        self.bus.on('recognizer_loop:audio_output_start',
                    self.on_audio_output_start)
        self.bus.on('recognizer_loop:audio_output_end',
                    self.on_audio_output_end)

        # other events
        self.bus.on("mycroft.awoken", self.on_awake)
        self.bus.on("speak", self.on_speak)
        self.bus.on("enclosure.notify.no_internet", self.on_no_internet)

        self._activate_mouth_events()

    def shutdown(self):
        """

        """
        self.bus.remove("enclosure.reset", self.on_reset)
        self.bus.remove("enclosure.system.reset", self.on_system_reset)
        self.bus.remove("enclosure.system.mute", self.on_system_mute)
        self.bus.remove("enclosure.system.unmute", self.on_system_unmute)
        self.bus.remove("enclosure.system.blink", self.on_system_blink)

        self.bus.remove("enclosure.eyes.on", self.on_eyes_on)
        self.bus.remove("enclosure.eyes.off", self.on_eyes_off)
        self.bus.remove("enclosure.eyes.blink", self.on_eyes_blink)
        self.bus.remove("enclosure.eyes.narrow", self.on_eyes_narrow)
        self.bus.remove("enclosure.eyes.look", self.on_eyes_look)
        self.bus.remove("enclosure.eyes.color", self.on_eyes_color)
        self.bus.remove("enclosure.eyes.brightness", self.on_eyes_brightness)
        self.bus.remove("enclosure.eyes.reset", self.on_eyes_reset)
        self.bus.remove("enclosure.eyes.timedspin", self.on_eyes_timed_spin)
        self.bus.remove("enclosure.eyes.volume", self.on_eyes_volume)
        self.bus.remove("enclosure.eyes.spin", self.on_eyes_spin)
        self.bus.remove("enclosure.eyes.set_pixel", self.on_eyes_set_pixel)

        self.bus.remove("enclosure.mouth.reset", self.on_display_reset)
        self.bus.remove("enclosure.mouth.talk", self.on_talk)
        self.bus.remove("enclosure.mouth.think", self.on_think)
        self.bus.remove("enclosure.mouth.listen", self.on_listen)
        self.bus.remove("enclosure.mouth.smile", self.on_smile)
        self.bus.remove("enclosure.mouth.viseme", self.on_viseme)
        self.bus.remove("enclosure.mouth.text", self.on_text)
        self.bus.remove("enclosure.mouth.display", self.on_display)
        self.bus.remove("enclosure.mouth.events.activate",
                        self._activate_mouth_events)
        self.bus.remove("enclosure.mouth.events.deactivate",
                        self._deactivate_mouth_events)

        self.bus.remove("enclosure.weather.display", self.on_weather_display)

        self.bus.remove("mycroft.awoken", self.on_awake)
        self.bus.remove("recognizer_loop:sleep", self.on_sleep)
        self.bus.remove("speak", self.on_speak)
        self.bus.remove('recognizer_loop:record_begin', self.on_record_begin)
        self.bus.remove('recognizer_loop:record_end', self.on_record_end)
        self.bus.remove('recognizer_loop:audio_output_start',
                        self.on_audio_output_start)
        self.bus.remove("enclosure.notify.no_internet", self.on_no_internet)

        self._deactivate_mouth_events()
        self._running = False

    def run(self):
        ''' start enclosure '''
        self._running = True
        while self._running:
            time.sleep(1)

    # Audio Events
    def on_record_begin(self, message=None):
        ''' listening started '''
        pass

    def on_record_end(self, message=None):
        ''' listening ended '''
        pass

    def on_audio_output_start(self, message=None):
        ''' speaking started '''
        pass

    def on_audio_output_end(self, message=None):
        ''' speaking started '''
        pass

    def on_awake(self, message=None):
        ''' on wakeup animation '''
        pass

    def on_sleep(self, message=None):
        ''' on naptime animation '''
        # TODO naptime skill animation should be ond here
        pass

    def on_speak(self, message=None):
        ''' on speak messages, intended for enclosures that disregard
        visemes '''
        pass

    def on_reset(self, message=None):
        """The enclosure should restore itself to a started state.
        Typically this would be represented by the eyes being 'open'
        and the mouth reset to its default (smile or blank).
        """
        pass

    # System Events
    def on_no_internet(self, message=None):
        """

        Args:
            message:
        """
        pass

    def on_system_reset(self, message=None):
        """The enclosure hardware should reset any CPUs, etc."""
        pass

    def on_system_mute(self, message=None):
        """Mute (turn off) the system speaker."""
        pass

    def on_system_unmute(self, message=None):
        """Unmute (turn on) the system speaker."""
        pass

    def on_system_blink(self, message=None):
        """The 'eyes' should blink the given number of times.
        Args:
            times (int): number of times to blink
        """
        pass

    # Eyes events
    def on_eyes_on(self, message=None):
        """Illuminate or show the eyes."""
        pass

    def on_eyes_off(self, message=None):
        """Turn off or hide the eyes."""
        pass

    def on_eyes_fill(self, message=None):
        pass

    def on_eyes_blink(self, message=None):
        """Make the eyes blink
        Args:
            side (str): 'r', 'l', or 'b' for 'right', 'left' or 'both'
        """
        pass

    def on_eyes_narrow(self, message=None):
        """Make the eyes look narrow, like a squint"""
        pass

    def on_eyes_look(self, message=None):
        """Make the eyes look to the given side
        Args:
            side (str): 'r' for right
                        'l' for left
                        'u' for up
                        'd' for down
                        'c' for crossed
        """
        pass

    def on_eyes_color(self, message=None):
        """Change the eye color to the given RGB color
        Args:
            r (int): 0-255, red value
            g (int): 0-255, green value
            b (int): 0-255, blue value
        """
        pass

    def on_eyes_brightness(self, message=None):
        """Set the brightness of the eyes in the display.
        Args:
            level (int): 1-30, bigger numbers being brighter
        """
        pass

    def on_eyes_reset(self, message=None):
        """Restore the eyes to their default (ready) state."""
        pass

    def on_eyes_timed_spin(self, message=None):
        """Make the eyes 'roll' for the given time.
        Args:
            length (int): duration in milliseconds of roll, None = forever
        """
        pass

    def on_eyes_volume(self, message=None):
        """Indicate the volume using the eyes
        Args:
            volume (int): 0 to 11
        """
        pass

    def on_eyes_spin(self, message=None):
        """
        Args:
        """
        pass

    def on_eyes_set_pixel(self, message=None):
        """
        Args:
        """
        pass

    # Mouth events
    def _on_mouth_reset(self, message=None):
        """Restore the mouth display to normal (blank)"""
        if self.mouth_events_active:
            self.on_display_reset(message)

    def _on_mouth_talk(self, message=None):
        """Show a generic 'talking' animation for non-synched speech"""
        if self.mouth_events_active:
            self.on_talk(message)

    def _on_mouth_think(self, message=None):
        """Show a 'thinking' image or animation"""
        if self.mouth_events_active:
            self.on_think(message)

    def _on_mouth_listen(self, message=None):
        """Show a 'thinking' image or animation"""
        if self.mouth_events_active:
            self.on_listen(message)

    def _on_mouth_smile(self, message=None):
        """Show a 'smile' image or animation"""
        if self.mouth_events_active:
            self.on_smile(message)

    def _on_mouth_viseme(self, message=None):
        """Display a viseme mouth shape for synched speech
        Args:
            code (int):  0 = shape for sounds like 'y' or 'aa'
                         1 = shape for sounds like 'aw'
                         2 = shape for sounds like 'uh' or 'r'
                         3 = shape for sounds like 'th' or 'sh'
                         4 = neutral shape for no sound
                         5 = shape for sounds like 'f' or 'v'
                         6 = shape for sounds like 'oy' or 'ao'
        """
        if self.mouth_events_active:
            self.on_viseme(message)

    def _on_mouth_text(self, message=None):
        """Display text (scrolling as needed)
        Args:
            text (str): text string to display
        """
        if self.mouth_events_active:
            self.on_text(message)

    def _on_mouth_display(self, message=None):
        if self.mouth_events_active:
            self.on_display(message)

    # Display (faceplate) events
    def on_display_reset(self, message=None):
        """Restore the mouth display to normal (blank)"""
        pass

    def on_talk(self, message=None):
        """Show a generic 'talking' animation for non-synched speech"""
        pass

    def on_think(self, message=None):
        """Show a 'thinking' image or animation"""
        pass

    def on_listen(self, message=None):
        """Show a 'thinking' image or animation"""
        pass

    def on_smile(self, message=None):
        """Show a 'smile' image or animation"""
        pass

    def on_viseme(self, message=None):
        """Display a viseme mouth shape for synched speech
        Args:
            code (int):  0 = shape for sounds like 'y' or 'aa'
                         1 = shape for sounds like 'aw'
                         2 = shape for sounds like 'uh' or 'r'
                         3 = shape for sounds like 'th' or 'sh'
                         4 = neutral shape for no sound
                         5 = shape for sounds like 'f' or 'v'
                         6 = shape for sounds like 'oy' or 'ao'
        """
        pass

    def on_text(self, message=None):
        """Display text (scrolling as needed)
        Args:
            text (str): text string to display
        """
        pass

    def on_display(self, message=None):
        """Display images on faceplate. Currently supports images up to 16x8,
           or half the face. You can use the 'x' parameter to cover the other
           half of the faceplate.
        Args:
            img_code (str): text string that encodes a black and white image
            x (int): x offset for image
            y (int): y offset for image
            refresh (bool): specify whether to clear the faceplate before
                            displaying the new image or not.
                            Useful if you'd like to display muliple images
                            on the faceplate at once.
        """
        pass

    def on_weather_display(self, message=None):
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
        pass

    @property
    def mouth_events_active(self):
        return self._mouth_events

    def _activate_mouth_events(self, message=None):
        """Enable movement of the mouth with speech"""
        self._mouth_events = True

    def _deactivate_mouth_events(self, message=None):
        """Disable movement of the mouth with speech"""
        self._mouth_events = False


