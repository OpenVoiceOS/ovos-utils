from setuptools import setup

setup(
    name='ovos_utils',
    version='0.0.10',
    packages=['ovos_utils',
              'ovos_utils.intents',
              'ovos_utils.sound',
              "ovos_utils.enclosure",
              'ovos_utils.enclosure.mark1',
              'ovos_utils.enclosure.mark1.eyes',
              'ovos_utils.enclosure.mark1.faceplate',
              'ovos_utils.skills',
              'ovos_utils.lang'],
    url='https://github.com/OpenVoiceOS/ovos_utils',
    install_requires=[
        "mycroft-messagebus-client",
        "pexpect",
        "pyxdg",
        "PyYAML",
        "kthread",
        "json_database",
        "requests",
        "inflection"],
    extras_require={
        "extras": ["phoneme_guesser", "colour", "rapidfuzz"]
    },
    include_package_data=True,
    license='Apache',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='collection of simple utilities for use across the mycroft ecosystem'
)
