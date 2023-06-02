import shutil
import unittest
from os import makedirs
from os.path import isdir, join, dirname
from threading import Event
from time import time
from unittest.mock import Mock


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

        test_dir = join(dirname(__file__), "test_watch")
        test_file = join(test_dir, "test.watch")
        makedirs(test_dir, exist_ok=True)

        # Test watch directory
        called = Event()
        callback = Mock(side_effect=lambda x: called.set())
        watcher = FileWatcher([test_dir], callback)
        with open(test_file, 'w+') as f:
            callback.assert_not_called()

        # Called on file close after creation
        self.assertTrue(called.wait(3))
        callback.assert_called_once()
        called.clear()
        with open(test_file, 'w+') as f:
            callback.assert_called_once()
        # Called again on file close
        self.assertTrue(called.wait(3))
        self.assertEqual(callback.call_count, 2)

        # Not called on directory creation
        callback.reset_mock()
        called.clear()
        makedirs(join(test_dir, "new_dir"))
        self.assertFalse(called.wait(3))
        callback.assert_not_called()

        # Not called on recursive file creation
        with open(join(test_dir, "new_dir", "file.txt"), 'w+') as f:
            callback.assert_not_called()
        self.assertFalse(called.wait(3))
        callback.assert_not_called()

        watcher.shutdown()

        # Test recursive watch
        called = Event()
        callback = Mock(side_effect=lambda x: called.set())
        watcher = FileWatcher([test_dir], callback, recursive=True,
                              ignore_creation=True)
        # Called on file change
        with open(join(test_dir, "new_dir", "file.txt"), 'w+') as f:
            callback.assert_not_called()
        self.assertTrue(called.wait(3))
        callback.assert_called_once()

        # Not called on file creation
        with open(join(test_dir, "new_dir", "new_file.txt"), 'w+') as f:
            callback.assert_called_once()
        self.assertTrue(called.wait(3))
        callback.assert_called_once()

        watcher.shutdown()

        # Test watch single file
        called.clear()
        callback = Mock(side_effect=lambda x: called.set())
        watcher = FileWatcher([test_file], callback)
        with open(test_file, 'w+') as f:
            callback.assert_not_called()
        # Called on file close after change
        self.assertTrue(called.wait(3))
        callback.assert_called_once()
        watcher.shutdown()

        # Test changes on callback
        contents = None
        changed = Event()

        def _on_change(fp):
            nonlocal contents
            self.assertEqual(fp, test_file)
            with open(fp, 'r') as f:
                contents = f.read()
            changed.set()

        watcher = FileWatcher([test_file], _on_change)
        now_time = time()
        with open(test_file, 'w') as f:
            f.write(f"test {now_time}")
        self.assertTrue(changed.wait(3))
        self.assertEqual(contents, f"test {now_time}")
        watcher.shutdown()

        shutil.rmtree(test_dir)

    def test_file_event_handler(self):
        from ovos_utils.file_utils import FileEventHandler
        from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileClosedEvent
        test_file = join(dirname(__file__), "test.watch")
        callback = Mock()

        # Test ignore creation callbacks
        handler = FileEventHandler(test_file, callback, True)
        handler.on_any_event(FileCreatedEvent(test_file))
        callback.assert_not_called()

        # Closed before modification (i.e. listener started while file open)
        handler.on_any_event(FileClosedEvent(test_file))
        callback.assert_not_called()

        # Modified
        handler.on_any_event(FileModifiedEvent(test_file))
        handler.on_any_event(FileModifiedEvent(test_file))
        callback.assert_not_called()
        # Closed triggers callback
        handler.on_any_event(FileClosedEvent(test_file))
        callback.assert_called_once()
        # Second close won't trigger callback
        handler.on_any_event(FileClosedEvent(test_file))
        callback.assert_called_once()

        # Test include creation callbacks
        callback.reset_mock()
        handler = FileEventHandler(test_file, callback, False)
        handler.on_any_event(FileCreatedEvent(test_file))
        callback.assert_not_called()

        # Modified
        handler.on_any_event(FileModifiedEvent(test_file))
        handler.on_any_event(FileModifiedEvent(test_file))
        callback.assert_not_called()
        # Closed triggers callback
        handler.on_any_event(FileClosedEvent(test_file))
        callback.assert_called_once()
        # Second close won't trigger callback
        handler.on_any_event(FileClosedEvent(test_file))
        callback.assert_called_once()
