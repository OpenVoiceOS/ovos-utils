import unittest
from os.path import isdir, isfile


class TestFileUtils(unittest.TestCase):
    def test_get_temp_path(self):
        from ovos_utils.file_utils import get_temp_path
        self.assertTrue(isdir(get_temp_path()))
        self.assertIsInstance(get_temp_path("test"), str)
        self.assertIsInstance(get_temp_path("test/1/2.test"), str)

    def test_get_cache_directory(self):
        from ovos_utils.file_utils import get_cache_directory
        self.assertTrue(isdir(get_cache_directory("test")))
        self.assertTrue(isdir(get_cache_directory("test/another/test")))

    def test_resolve_ovos_resource_file(self):
        from ovos_utils.file_utils import resolve_ovos_resource_file
        invalid = resolve_ovos_resource_file("not_real.file")
        self.assertIsNone(invalid)
        # TODO: Test valid case

    def test_resolve_resource_file(self):
        from ovos_utils.file_utils import resolve_resource_file
        # TODO

    def test_read_vocab_file(self):
        from ovos_utils.file_utils import read_vocab_file
        # TODO

    def test_load_regex_from_file(self):
        from ovos_utils.file_utils import load_regex_from_file
        # TODO

    def test_load_vocabulary(self):
        from ovos_utils.file_utils import load_vocabulary
        # TODO

    def test_load_regex(self):
        from ovos_utils.file_utils import load_regex
        # TODO

    def test_read_value_file(self):
        from ovos_utils.file_utils import read_value_file
        # TODO

    def test_read_translated_file(self):
        from ovos_utils.file_utils import read_translated_file
        # TODO

    def test_filewatcher(self):
        from ovos_utils.file_utils import FileWatcher
        # TODO

    def test_file_event_handler(self):
        from ovos_utils.file_utils import FileEventHandler
        # TODO
