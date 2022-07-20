import unittest
from os import environ
from os.path import isdir, join, dirname
from unittest.mock import patch


class TestLocations(unittest.TestCase):
    @patch("ovos_utils.skills.locations.get_plugin_skills")
    def test_get_installed_skill_ids(self, plugins):
        plugins.return_value = (['plugin_dir', 'plugin_dir_2'],
                                ['plugin_id', 'plugin_id_2'])
        from ovos_utils.skills.locations import get_installed_skill_ids
        environ["XDG_DATA_DIRS"] = join(dirname(__file__), "test_skills_xdg")
        config = {"skills": {
            "extra_directories": [join(dirname(__file__), "test_skills_dir")]
        }}
        skill_ids = get_installed_skill_ids(config)
        self.assertEqual(set(skill_ids), {"plugin_id", "plugin_id_2",
                                          "skill-test-1.openvoiceos",
                                          "skill-test-2.openvoiceos"})

    def test_get_skill_directories(self):
        from ovos_utils.skills.locations import get_skill_directories

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

    def test_get_default_skills_directory(self):
        from ovos_utils.skills.locations import get_default_skills_directory
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

    def test_get_plugin_skills(self):
        from ovos_utils.skills.locations import get_plugin_skills
        dirs, ids = get_plugin_skills()
        for d in dirs:
            self.assertTrue(isdir(d))
        for s in ids:
            self.assertIsInstance(s, str)
        self.assertEqual(len(dirs), len(ids))
