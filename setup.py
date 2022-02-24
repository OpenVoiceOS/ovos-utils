import os
from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    """ Find the version of the package"""
    version = None
    version_file = os.path.join(BASEDIR, 'ovos_utils', 'version.py')
    major, minor, build, alpha = (None, None, None, None)
    with open(version_file) as f:
        for line in f:
            if 'VERSION_MAJOR' in line:
                major = line.split('=')[1].strip()
            elif 'VERSION_MINOR' in line:
                minor = line.split('=')[1].strip()
            elif 'VERSION_BUILD' in line:
                build = line.split('=')[1].strip()
            elif 'VERSION_ALPHA' in line:
                alpha = line.split('=')[1].strip()

            if ((major and minor and build and alpha) or
                    '# END_VERSION_BLOCK' in line):
                break
    version = f"{major}.{minor}.{build}"
    if alpha and int(alpha) > 0:
        version += f"a{alpha}"
    return version


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


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
    version=get_version(),
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
    package_data={'': package_files('ovos_utils')},
    include_package_data=True,
    license='Apache',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='collection of simple utilities for use across the mycroft ecosystem'
)
