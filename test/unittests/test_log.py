import os
import shutil
import unittest
import importlib

from os.path import join, dirname, isdir, isfile
from unittest.mock import patch


class TestLog(unittest.TestCase):
    test_dir = join(dirname(__file__), "log_test")

    @classmethod
    def tearDownClass(cls) -> None:
        if isdir(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_log(self):
        import ovos_utils.log
        from ovos_utils.log import LOG
        # Default log config
        self.assertEqual(LOG.base_path, "stdout")
        self.assertIsInstance(LOG.fmt, str)
        self.assertIsInstance(LOG.datefmt, str)
        self.assertIsNotNone(LOG.formatter)
        self.assertIsInstance(LOG.max_bytes, int)
        self.assertIsInstance(LOG.backup_count, int)
        self.assertEqual(LOG.name, "OVOS")
        self.assertEqual(LOG.level, "INFO")
        self.assertFalse(LOG.diagnostic_mode)

        # Override from envvars
        os.environ["OVOS_DEFAULT_LOG_NAME"] = "test"
        os.environ["OVOS_DEFAULT_LOG_LEVEL"] = "DEBUG"
        importlib.reload(ovos_utils.log)
        from ovos_utils.log import LOG
        self.assertEqual(LOG.name, "test")
        self.assertEqual(LOG.level, "DEBUG")

        # init log
        test_config = {"path": self.test_dir,
                       "max_bytes": 100000,
                       "backup_count": 0,
                       "level": "WARNING",
                       "diagnostic": True}
        LOG.init(test_config)
        self.assertEqual(LOG.base_path, self.test_dir)
        self.assertEqual(LOG.max_bytes, 100000)
        self.assertEqual(LOG.backup_count, 0)
        self.assertEqual(LOG.level, "WARNING")
        self.assertTrue(LOG.diagnostic_mode)

        log_file = join(LOG.base_path, f"{LOG.name}.log")
        self.assertFalse(isfile(log_file))
        LOG.info("This won't print")
        self.assertTrue(isfile(log_file))
        LOG.warning("This will print")
        with open(log_file) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("This will print\n"))

    def test_init_service_logger(self):
        from ovos_utils.log import init_service_logger
        # TODO

    @patch("ovos_utils.log.LOG.warning")
    def test_log_deprecation(self, log_warning):
        from ovos_utils.log import log_deprecation

        log_deprecation("test")
        log_warning.assert_called_once()
        log_msg = log_warning.call_args[0][0]
        self.assertTrue(log_msg.startswith('test - unittest.mock'))

        log_deprecation()
        log_msg = log_warning.call_args[0][0]
        self.assertTrue(log_msg.startswith('DEPRECATED - unittest.mock'))

    @patch("ovos_utils.log.LOG.warning")
    def test_deprecated_decorator(self, log_warning):
        from ovos_utils.log import deprecated
        import sys
        sys.path.insert(0, dirname(__file__))
        from deprecation_helper import deprecated_function
        deprecated_function()
        log_warning.assert_called_once()
        log_msg = log_warning.call_args[0][0]
        self.assertTrue(log_msg.startswith('imported deprecation - test_log'))

        call_arg = None

        @deprecated("test deprecation")
        def _deprecated_function(test_arg):
            nonlocal call_arg
            call_arg = test_arg

        _deprecated_function("test")
        self.assertEqual(call_arg, "test")
        log_msg = log_warning.call_args[0][0]
        self.assertTrue(log_msg.startswith('test deprecation - '))
