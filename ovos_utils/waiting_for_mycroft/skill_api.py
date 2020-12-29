# https://github.com/MycroftAI/mycroft-core/pull/1822

# Copyright 2020 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Skill Api

The skill api allows skills interact with eachother over the message bus
just like interacting with any other object.
"""

try:
    from mycroft.messagebus.message import Message
except ImportError:
    import sys
    from ovos_utils.log import LOG
    from ovos_utils import get_mycroft_root
    MYCROFT_ROOT_PATH = get_mycroft_root()
    if MYCROFT_ROOT_PATH is not None:
        sys.path.append(MYCROFT_ROOT_PATH)
        try:
            from mycroft.messagebus.message import Message
        except ImportError:
            LOG.error("Could not find mycroft root path")
            from ovos_utils.messagebus import Message


def skill_api_method(func):
    """Decorator for adding a method to the skill's public api.
    Methods with this decorator will be registered on the message bus
    and an api object can be created for interaction with the skill.
    """
    # tag the method by adding an api_method member to it
    if not hasattr(func, 'api_method') and hasattr(func, '__name__'):
        func.api_method = True
    return func


class SkillApi:
    """SkillApi providing a simple interface to exported methods from skills

    Methods are built from a method_dict provided when initializing the skill.
    """
    bus = None

    @classmethod
    def connect_bus(cls, mycroft_bus):
        """Registers the bus object to use."""
        # PATCH - in mycroft-core this would be called only once
        # in here it is done in MycroftSkill.bind so i added this
        # conditional check
        if cls.bus is None and mycroft_bus is not None:
            cls.bus = mycroft_bus

    def __init__(self, method_dict):
        self.method_dict = method_dict
        for key in method_dict:
            def get_method(k):
                def method(*args, **kwargs):
                    m = self.method_dict[k]
                    data = {'args': args, 'kwargs': kwargs}
                    method_msg = Message(m['type'], data)
                    response = SkillApi.bus.wait_for_response(method_msg)
                    if (response and response.data and
                            'result' in response.data):
                        return response.data['result']
                    else:
                        return None

                return method

            self.__setattr__(key, get_method(key))

    @staticmethod
    def get(skill):
        """Generate api object from skill id.
        Arguments:
            skill (str): skill id for target skill

        Returns:
            SkillApi
        """
        public_api_msg = '{}.public_api'.format(skill)
        api = SkillApi.bus.wait_for_response(Message(public_api_msg))
        if api:
            return SkillApi(api.data)
        else:
            return None

