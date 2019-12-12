from setuptools import setup

setup(
    name='jarbas_utils',
    version='0.2.0',
    packages=['jarbas_utils', 'jarbas_utils.sound', 'jarbas_utils.system'],
    url='https://github.com/JarbasAl/jarbas_utils',
    install_requires=["pronouncing",
                      "googletrans",
                      "pyalsaaudio==0.8.2",
                      "mycroft-messagebus-client"],
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='collection of simple utilities for use across the mycroft ecosystem'
)
