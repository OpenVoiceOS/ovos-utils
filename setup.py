from setuptools import setup

setup(
    name='ovos_utils',
    version='0.0.2',
    packages=['ovos_utils',
              'ovos_utils.sound',
              'ovos_utils.mark1',
              'ovos_utils.skills',
              'ovos_utils.lang'],
    url='https://github.com/OpenVoiceOS/ovos_utils',
    install_requires=["pronouncing",
                      "mycroft-messagebus-client",
                      "inflection",
                      "colour",
                      "pexpect",
                      "requests"],
    license='Apache',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='collection of simple utilities for use across the mycroft ecosystem'
)
