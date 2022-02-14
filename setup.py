import os
from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


setup(
    name='ovos_utils',
    version='0.0.14a7',
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
    install_requires=required("requirements/requirements.txt"),
    extras_require={
        "extras": required("requirements/extras.txt")
    },
    include_package_data=True,
    license='Apache',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='collection of simple utilities for use across the mycroft ecosystem'
)
