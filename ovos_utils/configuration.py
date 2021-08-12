import json
import os
from os import makedirs
from os.path import isfile, exists, expanduser, join, dirname, isdir

from xdg import BaseDirectory as XDG

from ovos_utils.fingerprinting import core_supports_xdg
from ovos_utils.json_helper import merge_dict, load_commented_json
from ovos_utils.log import LOG
from ovos_utils.system import search_mycroft_core_location

# for downstream support, all XDG paths should respect this
_BASE_FOLDER = "mycroft"
_CONFIG_FILE_NAME = "mycroft.conf"

_DEFAULT_CONFIG = None
_SYSTEM_CONFIG = os.environ.get('MYCROFT_SYSTEM_CONFIG',
                                f'/etc/{_BASE_FOLDER}/{_CONFIG_FILE_NAME}')
# Make sure we support the old location until mycroft moves to XDG
_OLD_USER_CONFIG = join(expanduser('~'), '.' + _BASE_FOLDER, _CONFIG_FILE_NAME)
_USER_CONFIG = join(XDG.xdg_config_home, _BASE_FOLDER, _CONFIG_FILE_NAME)
_WEB_CONFIG_CACHE = join(XDG.xdg_config_home, _BASE_FOLDER, 'web_cache.json')


def get_xdg_base():
    global _BASE_FOLDER
    return _BASE_FOLDER


def set_xdg_base(folder_name):
    global _BASE_FOLDER, _WEB_CONFIG_CACHE
    LOG.info(f"XDG base folder set to: '{folder_name}'")
    _BASE_FOLDER = folder_name
    _WEB_CONFIG_CACHE = join(XDG.xdg_config_home, _BASE_FOLDER,
                             'web_cache.json')


def set_config_filename(file_name, core_folder=None):
    global _CONFIG_FILE_NAME, _SYSTEM_CONFIG, _OLD_USER_CONFIG, _USER_CONFIG, \
        _BASE_FOLDER
    if core_folder:
        _BASE_FOLDER = core_folder
        set_xdg_base(core_folder)
    LOG.info(f"config filename set to: '{file_name}'")
    _CONFIG_FILE_NAME = file_name
    _SYSTEM_CONFIG = os.environ.get('MYCROFT_SYSTEM_CONFIG',
                                    f'/etc/{_BASE_FOLDER}/{_CONFIG_FILE_NAME}')
    # Make sure we support the old location still
    # Deprecated and will be removed eventually
    _OLD_USER_CONFIG = join(expanduser('~'), '.' + _BASE_FOLDER,
                            _CONFIG_FILE_NAME)
    _USER_CONFIG = join(XDG.xdg_config_home, _BASE_FOLDER, _CONFIG_FILE_NAME)


def set_default_config(file_path=None):
    global _DEFAULT_CONFIG
    _DEFAULT_CONFIG = file_path or find_default_config()
    LOG.info(f"default config file changed to: {file_path}")


def find_default_config():
    if _DEFAULT_CONFIG:
        # previously set, otherwise None
        return _DEFAULT_CONFIG
    mycroft_root = search_mycroft_core_location()
    if not mycroft_root:
        raise FileNotFoundError("Couldn't find mycroft core root folder.")
    return join(mycroft_root, _BASE_FOLDER, "configuration", _CONFIG_FILE_NAME)


def find_user_config():
    # ideally it will have been set by downstream using util methods
    old, path = get_config_locations(default=False, web_cache=False,
                                     system=False, old_user=True,
                                     user=True)
    if isfile(path):
        return path

    if core_supports_xdg():
        path = join(XDG.xdg_config_home, _BASE_FOLDER, _CONFIG_FILE_NAME)
    else:
        path = old
        # mark1 runs as a different user
        sysconfig = MycroftSystemConfig()
        platform_str = sysconfig.get("enclosure", {}).get("platform", "")
        if platform_str == "mycroft_mark_1":
            path = "/home/mycroft/.mycroft/mycroft.conf"

    if not isfile(path) and isfile(old):
        # xdg might be disabled in HolmesV compatibility mode
        # or migration might be in progress
        # (user action required when updated from a no xdg install)
        path = old

    return path


def get_config_locations(default=True, web_cache=True, system=True,
                         old_user=True, user=True):
    locs = []
    if default:
        locs.append(_DEFAULT_CONFIG)
    if system:
        locs.append(_SYSTEM_CONFIG)
    if web_cache:
        locs.append(_WEB_CONFIG_CACHE)
    if old_user:
        locs.append(_OLD_USER_CONFIG)
    if user:
        locs.append(_USER_CONFIG)

    return locs


def get_webcache_location():
    return join(XDG.xdg_config_home, _BASE_FOLDER, _CONFIG_FILE_NAME)


def get_xdg_config_locations():
    # This includes both the user config and
    # /etc/xdg/mycroft/mycroft.conf
    xdg_paths = list(reversed(
        [join(p, get_config_filename())
         for p in XDG.load_config_paths(get_xdg_base())]
    ))
    return xdg_paths


def get_config_filename():
    return _CONFIG_FILE_NAME


def set_config_name(name, core_folder=None):
    # TODO deprecate, was only out in a couple versions
    # renamed to match HolmesV
    set_config_filename(name, core_folder)


def read_mycroft_config():
    conf = LocalConf(None)
    conf.merge(MycroftDefaultConfig())
    conf.merge(MycroftSystemConfig())
    conf.merge(MycroftUserConfig())
    return conf


def update_mycroft_config(config, path=None):
    if path is None:
        conf = MycroftUserConfig()
    else:
        conf = LocalConf(path)
    conf.merge(config)
    conf.store()
    return conf


class LocalConf(dict):
    """
        Config dict from file.
    """
    allow_overwrite = True

    def __init__(self, path):
        super(LocalConf, self).__init__()
        self.path = path
        if self.path:
            self.load_local(self.path)

    def load_local(self, path):
        """
            Load local json file into self.

            Args:
                path (str): file to load
        """
        path = expanduser(path)
        if exists(path) and isfile(path):
            try:
                config = load_commented_json(path)
                for key in config:
                    self.__setitem__(key, config[key])
                #LOG.debug("Configuration {} loaded".format(path))
            except Exception as e:
                LOG.error("Error loading configuration '{}'".format(path))
                LOG.error(repr(e))
        else:
            pass
            #LOG.debug("Configuration '{}' not defined, skipping".format(path))

    def reload(self):
        self.load_local(self.path)

    def store(self, path=None):
        """
            store the configuration locally.
        """
        path = path or self.path
        if not path:
            LOG.warning("config path not set, updating user config!!")
            update_mycroft_config(self)
            return
        path = expanduser(path)
        if not isdir(dirname(path)):
            makedirs(dirname(path))
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(self, f, indent=4, ensure_ascii=False)

    def merge(self, conf):
        merge_dict(self, conf)
        return self


class ReadOnlyConfig(LocalConf):
    """ read only  """

    def __init__(self, path, allow_overwrite=False):
        super().__init__(path)
        self.allow_overwrite = allow_overwrite

    def reload(self):
        old = self.allow_overwrite
        self.allow_overwrite = True
        super().reload()
        self.allow_overwrite = old

    def __setitem__(self, key, value):
        if not self.allow_overwrite:
            raise PermissionError
        super().__setitem__(key, value)

    def __setattr__(self, key, value):
        if not self.allow_overwrite:
            raise PermissionError
        super().__setattr__(key, value)

    def merge(self, conf):
        if not self.allow_overwrite:
            raise PermissionError
        super().merge(conf)

    def store(self, path=None):
        if not self.allow_overwrite:
            raise PermissionError
        super().store(path)


class MycroftUserConfig(LocalConf):
    def __init__(self):
        path = find_user_config()
        super().__init__(path)


class MycroftDefaultConfig(ReadOnlyConfig):
    def __init__(self):
        path = find_default_config()
        super().__init__(path)
        if not self.path or not isfile(self.path):
            LOG.error("mycroft root path not found, could not load default "
                      ".conf")

    def set_root_config_path(self, root_config):
        # in case we got it wrong / non standard
        self.path = root_config
        self.reload()


class MycroftSystemConfig(ReadOnlyConfig):
    def __init__(self, allow_overwrite=False):
        path = get_config_locations(default=False, web_cache=False,
                                    system=True, old_user=False,
                                    user=False)[0]
        super().__init__(path, allow_overwrite)


class MycroftXDGConfig(LocalConf):
    def __init__(self):
        path = get_config_locations(default=False, web_cache=False,
                                    system=False, old_user=False,
                                    user=True)[0]
        super().__init__(path)
