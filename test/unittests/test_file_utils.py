import os
import shutil
import unittest
from os import makedirs
from os.path import isdir, join, dirname
from threading import Event
from time import time
from unittest.mock import Mock, patch


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

    def test_filewatcher_not_yet_existing_file(self):
        from ovos_utils.file_utils import FileWatcher

        test_dir = join(dirname(__file__), "test_watch_new")
        test_file = join(test_dir, "not_yet.watch")
        makedirs(test_dir, exist_ok=True)
        self.assertFalse(os.path.isfile(test_file))

        # a path that doesn't exist yet is still watched in file mode:
        # the containing (existing) directory is scheduled, and a
        # 'created' event for the not-yet-existing file fires the callback
        called = Event()
        callback = Mock(side_effect=lambda x: called.set())
        watcher = FileWatcher([test_file], callback)
        with open(test_file, 'w+'):
            pass
        self.assertTrue(called.wait(3))
        callback.assert_called_once_with(test_file)
        watcher.shutdown()

        # a different file being created in the same directory must
        # NOT fire the callback (file mode still filters to the one path)
        called.clear()
        callback.reset_mock()
        watcher = FileWatcher([test_file], callback)
        other_file = join(test_dir, "other.watch")
        with open(other_file, 'w+'):
            pass
        self.assertFalse(called.wait(3))
        callback.assert_not_called()
        watcher.shutdown()

        shutil.rmtree(test_dir)

    def test_filewatcher_missing_parent_directory(self):
        from ovos_utils.file_utils import FileWatcher

        # if the parent directory of a not-yet-existing file also doesn't
        # exist, watchdog can't schedule an observer on it; FileWatcher
        # must skip that entry (with a LOG.warning) instead of raising
        # an opaque watchdog exception
        missing_parent = join(dirname(__file__), "definitely_not_there")
        missing_file = join(missing_parent, "cfg.json")
        self.assertFalse(isdir(missing_parent))

        callback = Mock()
        with patch("ovos_utils.file_utils.LOG") as mock_log:
            watcher = FileWatcher([missing_file], callback)
            mock_log.warning.assert_called_once()
        self.assertEqual(watcher.observer.emitters, set())
        watcher.shutdown()

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

        # Test events for a different file in the same directory are ignored
        # when watching a specific file (the FileWatcher watches the
        # containing directory, so watchdog reports every file inside it)
        other_file = join(dirname(__file__), "other.watch")
        callback.reset_mock()
        handler = FileEventHandler(test_file, callback, True)
        handler.on_any_event(FileModifiedEvent(other_file))
        handler.on_any_event(FileClosedEvent(other_file))
        callback.assert_not_called()
        # but the watched file itself still fires
        handler.on_any_event(FileModifiedEvent(test_file))
        handler.on_any_event(FileClosedEvent(test_file))
        callback.assert_called_once()

        # Test directory-watch mode (file_path=None) reports every file
        callback.reset_mock()
        handler = FileEventHandler(None, callback, True)
        handler.on_any_event(FileModifiedEvent(test_file))
        handler.on_any_event(FileClosedEvent(test_file))
        callback.assert_called_once_with(test_file)
        callback.reset_mock()
        handler.on_any_event(FileModifiedEvent(other_file))
        handler.on_any_event(FileClosedEvent(other_file))
        callback.assert_called_once_with(other_file)

        # Test two handlers watching different files in the same directory
        # each fire only for their own file, not for each other's
        callback_a = Mock()
        callback_b = Mock()
        handler_a = FileEventHandler(test_file, callback_a, True)
        handler_b = FileEventHandler(other_file, callback_b, True)
        # both handlers watch the same directory, so watchdog delivers
        # every event to both of them
        for handler in (handler_a, handler_b):
            for ev_file in (test_file, other_file):
                handler.on_any_event(FileModifiedEvent(ev_file))
                handler.on_any_event(FileClosedEvent(ev_file))
        callback_a.assert_called_once_with(test_file)
        callback_b.assert_called_once_with(other_file)

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
