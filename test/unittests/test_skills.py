import unittest
from os import environ
from os.path import isdir, join, dirname, basename
from unittest.mock import patch

from ovos_utils.fakebus import FakeBus, Message
from ovos_utils.skills.locations import get_skill_directories
from ovos_utils.skills.locations import get_default_skills_directory
from ovos_utils.skills.locations import get_installed_skill_ids
from ovos_utils.skills.locations import get_plugin_skills

try:
    import ovos_config
except ImportError:
    ovos_config = None


def _api_method_1(message: Message) -> str:
    return message.serialize()


def _api_method_2(**kwargs) -> int:
    return len(kwargs)


class TestSkills(unittest.TestCase):
    def test_get_non_properties(self):
        from ovos_utils.skills import get_non_properties
        # TODO

    def test_skills_loaded(self):
        from ovos_utils.skills import skills_loaded
        # TODO

    @patch("ovos_utils.skills.update_mycroft_config")
    def test_blacklist_skill(self, update_config):
        from ovos_utils.skills import blacklist_skill
        # TODO

    @patch("ovos_utils.skills.update_mycroft_config")
    def test_whitelist_skill(self, update_config):
        from ovos_utils.skills import whitelist_skill
        # TODO


class TestAudioservice(unittest.TestCase):
    def test_ensure_uri(self):
        from ovos_utils.skills.audioservice import ensure_uri
        valid_uri = "file:///test"
        non_uri = "/test"
        # rel_uri = "test"
        self.assertEqual(ensure_uri(valid_uri), valid_uri)
        self.assertEqual(ensure_uri(non_uri), valid_uri)
        # TODO: Relative path is relative to method and not caller?
        # self.assertEqual(ensure_uri(rel_uri),
        #                  f"file://{join(dirname(__file__), 'test')}")

    def test_classic_audio_service_interface(self):
        from ovos_utils.skills.audioservice import ClassicAudioServiceInterface
        # TODO

    def test_audio_service_interface(self):
        from ovos_utils.skills.audioservice import AudioServiceInterface
        # TODO

    def test_ocp_interface(self):
        from ovos_utils.skills.audioservice import OCPInterface
        # TODO


class TestLocations(unittest.TestCase):
    @patch("ovos_plugin_manager.skills.get_plugin_skills")
    def test_get_installed_skill_ids(self, plugins):
        plugins.return_value = (['plugin_dir', 'plugin_dir_2'],
                                ['plugin_id', 'plugin_id_2'])
        environ["XDG_DATA_DIRS"] = join(dirname(__file__), "test_skills_xdg")
        config = {"skills": {
            "extra_directories": [join(dirname(__file__), "test_skills_dir")]
        }}
        skill_ids = get_installed_skill_ids(config)
        self.assertEqual(set(skill_ids), {"plugin_id", "plugin_id_2",
                                          "skill-test-1.openvoiceos",
                                          "skill-test-2.openvoiceos"})

    def test_get_skill_directories(self):
        if not ovos_config:
            return  # skip test since ovos.conf isn't taken into account

        # Default behavior, only one valid XDG path
        environ["XDG_DATA_DIRS"] = environ["XDG_DATA_HOME"] = \
            join(dirname(__file__), "test_skills_xdg")
        config = {"skills": {"extra_directories": []}}
        default_dir = join(dirname(__file__), "test_skills_xdg",
                           "mycroft", "skills")
        self.assertEqual(get_skill_directories(config), [default_dir])

        # Define single extra directory to append
        extra_dir = join(dirname(__file__), "test_skills_dir")
        config['skills']['extra_directories'] = [extra_dir]
        self.assertEqual(get_skill_directories(config),
                         [default_dir, extra_dir])

        # Define duplicated directories in extra_directories
        config['skills']['extra_directories'] += [extra_dir, default_dir]
        self.assertEqual(get_skill_directories(config),
                         [default_dir, extra_dir])

        # Define invalid directories in extra_directories
        config['skills']['extra_directories'] += ["/not/a/directory"]
        self.assertEqual(get_skill_directories(config),
                         [default_dir, extra_dir])

        # Default directory
        mock_config = {'skills': {}}
        default_directories = get_skill_directories(mock_config)
        for directory in default_directories:
            self.assertEqual(basename(directory), 'skills')
        # Configured directory
        mock_config['skills']['directory'] = 'test'
        test_directories = get_skill_directories(mock_config)
        for directory in test_directories:
            self.assertEqual(basename(directory), 'test')
        self.assertEqual(len(default_directories), len(test_directories))
        # Extra directory
        extra_dir = join(dirname(__file__), 'skills')
        mock_config['skills']['extra_directories'] = [extra_dir]
        extra_directories = get_skill_directories(mock_config)
        self.assertEqual(extra_directories[-1], extra_dir)
        for directory in test_directories:
            self.assertIn(directory, extra_directories)

    def test_get_default_skills_directory(self):
        if not ovos_config:
            return  # skip test since ovos.conf isn't taken into account
        test_skills_dir = join(dirname(__file__), "test_skills_dir")

        # Configured override (legacy)
        config = {"skills": {"directory_override": test_skills_dir}}
        self.assertEqual(get_default_skills_directory(config), test_skills_dir)

        # Configured extra_directories
        config = {"skills": {"extra_directories": [test_skills_dir, "/tmp"]}}
        self.assertEqual(get_default_skills_directory(config), test_skills_dir)

        environ["XDG_DATA_HOME"] = join(dirname(__file__), "test_skills_xdg")
        xdg_skills_dir = join(dirname(__file__), "test_skills_xdg",
                              "mycroft", "skills")
        # XDG (undefined extra_directories)
        config = {"skills": {}}
        self.assertEqual(get_default_skills_directory(config), xdg_skills_dir)

        # XDG (empty extra_directories)
        config = {"skills": {"extra_directories": []}}
        self.assertEqual(get_default_skills_directory(config), xdg_skills_dir)

        # Default directory
        mock_config = {'skills': {}}
        default_dir = get_default_skills_directory(mock_config)
        self.assertTrue(isdir(default_dir))
        self.assertEqual(basename(default_dir), 'skills')
        self.assertEqual(dirname(dirname(default_dir)),
                         join(dirname(__file__), "test_skills_xdg"))
        # Override directory
        mock_config['skills']['directory'] = 'test'
        test_dir = get_default_skills_directory(mock_config)
        self.assertTrue(isdir(test_dir))
        self.assertEqual(basename(test_dir), 'test')
        self.assertEqual(dirname(dirname(test_dir)),
                         join(dirname(__file__), "test_skills_xdg"))

    def test_get_plugin_skills(self):
        dirs, ids = get_plugin_skills()
        for d in dirs:
            self.assertTrue(isdir(d))
        for s in ids:
            self.assertIsInstance(s, str)
        self.assertEqual(len(dirs), len(ids))


class TestSkillApi(unittest.TestCase):
    from ovos_utils.skills.api import SkillApi
    bus = FakeBus()
    SkillApi.connect_bus(bus)

    def test_skill_api_init(self):
        from ovos_utils.skills.api import SkillApi
        test_api = SkillApi({"serialize": {'help': '',
                                           'type': 'test._api_method_1'},
                             "get_length": {'help': '',
                                            'type': 'test._api_method_2'}})
        self.assertEqual(test_api.bus, self.bus)
        self.assertEqual(SkillApi.bus, self.bus)
        self.assertIsNotNone(test_api.serialize)
        self.assertIsNotNone(test_api.get_length)
        self.assertTrue(callable(test_api.serialize))
        self.assertTrue(callable(test_api.get_length))

    def test_skill_api_get(self):
        from ovos_utils.skills.api import SkillApi

        def _valid_public_api(message):
            self.bus.emit(message.response(
                {"serialize": {'help': '', 'type': 'test._api_method_1'},
                 "get_length": {'help': '', 'type': 'test._api_method_2'}}))

        self.bus.on("test_skill.public_api", _valid_public_api)

        # Test get valid API
        api = SkillApi.get("test_skill")
        self.assertIsInstance(api, SkillApi)
        self.assertTrue(callable(api.serialize))
        self.assertTrue(callable(api.get_length))

        # Test second API
        api2 = SkillApi.get("test_skill")
        self.assertEqual(api.method_dict, api2.method_dict)

        # Test invalid API
        self.assertIsNone(SkillApi.get("other_skill"))

        # Test get without bus
        SkillApi.bus = None
        with self.assertRaises(RuntimeError):
            SkillApi.get("test_skill")
        SkillApi.connect_bus(self.bus)
