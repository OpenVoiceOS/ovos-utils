import os
import shutil
import unittest
import importlib
from copy import deepcopy

from os.path import join, dirname, isdir, isfile
from unittest.mock import patch, Mock


class TestLog(unittest.TestCase):
    test_dir = join(dirname(__file__), "log_test")

    @classmethod
    def tearDownClass(cls) -> None:
        if isdir(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_log(self):
        import ovos_utils.log
        importlib.reload(ovos_utils.log)
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

        # Init with backup
        test_config['max_bytes'] = 2
        test_config['backup_count'] = 1
        test_config['level'] = 'INFO'
        LOG.init(test_config)
        LOG.name = "rotate"
        LOG.info("first")
        LOG.info("second")
        LOG.debug("third")
        log_1 = join(LOG.base_path, f"{LOG.name}.log.1")
        log = join(LOG.base_path, f"{LOG.name}.log")

        # Log rotated once
        with open(log_1) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("first\n"))
        with open(log) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("second\n"))

        LOG.info("fourth")
        # Log rotated again
        with open(log_1) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("second\n"))
        with open(log) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("fourth\n"))

        # Multiple log rotations within a short period of time
        for i in range(100):
            LOG.info(str(i))
        with open(log_1) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("98\n"))
        with open(log) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("99\n"))

    @patch("ovos_utils.log.get_logs_config")
    @patch("ovos_config.Configuration.set_config_watcher")
    def test_init_service_logger(self, set_config_watcher, log_config):
        from ovos_utils.log import init_service_logger, LOG

        # Test log init with default config
        log_config.return_value = dict()
        LOG.level = "ERROR"
        init_service_logger("default")
        from ovos_utils.log import LOG
        set_config_watcher.assert_called_once()
        self.assertEqual(LOG.name, "default")
        self.assertEqual(LOG.level, "ERROR")

        # Test log init with config
        set_config_watcher.reset_mock()
        log_config.return_value = {"path": self.test_dir,
                                   "level": "DEBUG"}
        init_service_logger("configured")
        from ovos_utils.log import LOG
        set_config_watcher.assert_called_once()
        self.assertEqual(LOG.name, "configured")
        self.assertEqual(LOG.level, "DEBUG")
        LOG.debug("This will print")
        self.assertTrue(isfile(join(self.test_dir, "configured.log")))

    @patch("ovos_utils.log.LOG.create_logger")
    def test_log_deprecation(self, create_logger):
        fake_log = Mock()
        log_warning = fake_log.warning
        create_logger.return_value = fake_log
        from ovos_utils.log import log_deprecation

        log_deprecation("test")
        create_logger.assert_called_once()
        log_msg = log_warning.call_args[0][0]
        self.assertIn('version=Unknown', log_msg, log_msg)
        self.assertIn('test', log_msg, log_msg)

        log_deprecation()
        log_msg = log_warning.call_args[0][0]
        self.assertIn('version=Unknown', log_msg, log_msg)
        self.assertIn('DEPRECATED', log_msg, log_msg)

    @patch("ovos_utils.log.LOG.create_logger")
    def test_deprecated_decorator(self, create_logger):
        fake_log = Mock()
        log_warning = fake_log.warning
        create_logger.return_value = fake_log
        from ovos_utils.log import deprecated
        import sys
        sys.path.insert(0, dirname(__file__))
        from deprecation_helper import deprecated_function, Deprecated
        deprecated_function()
        log_warning.assert_called_once()
        log_msg = log_warning.call_args[0][0]
        self.assertIn('version=0.1.0', log_msg, log_msg)
        self.assertIn('test_log', log_msg, log_msg)
        self.assertIn('imported deprecation', log_msg, log_msg)

        test_class = Deprecated()
        log_msg = log_warning.call_args[0][0]
        self.assertIn('version=0.2.0', log_msg, log_msg)
        self.assertIn('Class Deprecated', log_msg, log_msg)

        call_arg = None

        @deprecated("test deprecation", "1.0.0")
        def _deprecated_function(test_arg):
            nonlocal call_arg
            call_arg = test_arg

        _deprecated_function("test")
        self.assertEqual(call_arg, "test")
        log_msg = log_warning.call_args[0][0]
        self.assertIn('version=1.0.0', log_msg, log_msg)
        self.assertIn('test deprecation', log_msg, log_msg)

    @patch("ovos_utils.log.get_logs_config")
    @patch("ovos_utils.log.LOG")
    def test_monitor_log_level(self, log, get_config):
        from ovos_utils.log import _monitor_log_level

        log.name = "TEST"
        get_config.return_value = {"changed": False}

        _monitor_log_level()
        get_config.assert_called_once_with("TEST")
        log.init.assert_called_once_with(get_config.return_value)
        log.info.assert_called_once()

        # Callback with no change
        _monitor_log_level()
        self.assertEqual(get_config.call_count, 2)
        log.init.assert_called_once_with(get_config.return_value)
        log.info.assert_called_once()

        # Callback with change
        get_config.return_value["changed"] = True
        _monitor_log_level()
        self.assertEqual(get_config.call_count, 3)
        self.assertEqual(log.init.call_count, 2)
        log.init.assert_called_with(get_config.return_value)

    def test_get_logs_config(self):
        from ovos_utils.log import get_logs_config
        valid_config = {"level": "DEBUG",
                        "path": self.test_dir,
                        "max_bytes": 1000,
                        "backup_count": 2,
                        "diagnostic": False}
        valid_config_2 = {"max_bytes": 100000,
                          "diagnostic": True}
        logs_config = {"path": self.test_dir,
                       "max_bytes": 1000,
                       "backup_count": 2,
                       "diagnostic": False}
        legacy_config = {"log_level": "DEBUG",
                         "logs": logs_config}

        logging_config = {"logging": {"log_level": "DEBUG",
                                      "logs": logs_config,
                                      "test_service": {"log_level": "WARNING",
                                                       "logs": valid_config_2}
                                      }
                          }

        # Test original config with `logs` section and no `logging` section
        self.assertEqual(get_logs_config("", legacy_config), valid_config)

        # Test `logging.logs` config with no service config
        self.assertEqual(get_logs_config("service", logging_config), valid_config)

        # Test `logging.logs` config with `logging.<service>` overrides
        expected_config = {**valid_config_2, **{"level": "WARNING"}}
        self.assertEqual(get_logs_config("test_service", logging_config),
                         expected_config)

        # Test `logs` config with `logging.<service>` overrides
        logging_config["logs"] = logging_config["logging"].pop("logs")
        self.assertEqual(get_logs_config("test_service", logging_config),
                         expected_config)

        # Test `logging.<service>` config with no `logs` or `logging.logs`
        logging_config["logging"].pop("log_level")
        logging_config.pop("logs")
        self.assertEqual(get_logs_config("test_service", logging_config),
                         expected_config)

    @patch("ovos_utils.log.get_logs_config")
    def test_get_log_path(self, get_config):
        from ovos_utils.log import get_log_path

        real_log_path = join(dirname(__file__), "test_logs")
        test_paths = [self.test_dir, dirname(__file__), real_log_path]

        # Test with multiple populated directories
        self.assertEqual(get_log_path("real", test_paths), real_log_path)
        self.assertIsNone(get_log_path("fake", test_paths))

        # Test path from configuration
        get_config.return_value = {"path": self.test_dir}
        self.assertEqual(get_log_path("test"), self.test_dir)
        get_config.assert_called_once_with(service_name="test")

    @patch('ovos_config.Configuration')
    def test_get_log_paths(self, config):
        from ovos_utils.log import get_log_paths

        config_no_modules = {"logging": {"logs": {"path": "default_path"}}}

        # Test default config path from Configuration (no module overrides)
        config.return_value = config_no_modules
        self.assertEqual(get_log_paths(), {"default_path"})

        # Test services with different configured paths
        config_multi_modules = {"logging": {"logs": {"path": "default_path"},
                                            "module_1": {"path": "path_1"},
                                            "module_2": {"path": "path_2"},
                                            "module_3": {"path": "path_1"}}}
        self.assertEqual(get_log_paths(config_multi_modules),
                         {"default_path", "path_1", "path_2"})


    @patch('ovos_utils.log.get_log_paths')
    def test_get_available_logs(self, get_log_paths):
        from ovos_utils.log import get_available_logs

        # Test with specified directories containing logs and other files
        real_log_path = join(dirname(__file__), "test_logs")
        get_log_paths.return_value = [dirname(__file__), real_log_path]
        self.assertEqual(get_available_logs(), ["real"])

        # Test with no log directories
        self.assertEqual(get_available_logs([dirname(__file__)]), [])
        get_log_paths.return_value = []
        self.assertEqual(get_available_logs(), [])
