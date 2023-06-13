import json
from os import makedirs
from os.path import join, expanduser, exists, isfile

import ovos_utils.xdg_utils as xdg
from ovos_utils.log import LOG, deprecated


# TODO - deprecate this submodule in 0.1.0
# note that a couple of these are also used inside ovos-utils
# perhaps those usages should also move into workshop ?

@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_default_lang():
    try:
        from ovos_config.locale import get_default_lang as _get
        return _get()
    except ImportError:
        return read_mycroft_config().get("lang", "en-us")


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def find_user_config():
    try:
        from ovos_config.locations import find_user_config as _get
        return _get()
    except ImportError:

        return join(get_xdg_config_save_path(), get_config_filename())


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_webcache_location():
    return join(get_xdg_config_save_path(), 'web_cache.json')


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_config_locations(default=True, web_cache=True, system=True,
                         old_user=True, user=True):
    try:
        from ovos_config.locations import get_config_locations as _get
        return _get(default, web_cache, system, old_user, user)
    except ImportError:
        locs = []
        ovos_cfg = get_ovos_config()
        if default:
            locs.append(ovos_cfg["default_config_path"])
        if system:
            locs.append(f"/etc/{ovos_cfg['base_folder']}/{ovos_cfg['config_filename']}")
        if web_cache:
            locs.append(get_webcache_location())
        if old_user:
            locs.append(f"~/.{ovos_cfg['base_folder']}/{ovos_cfg['config_filename']}")
        if user:
            locs.append(f"{get_xdg_config_save_path()}/{ovos_cfg['config_filename']}")
        return locs


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_ovos_config():
    try:
        from ovos_config.meta import get_ovos_config as _get
        return _get()
    except ImportError:
        return {"xdg": True,
                "base_folder": "mycroft",
                "config_filename": "mycroft.conf"}


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_xdg_base():
    try:
        from ovos_config.meta import get_xdg_base as _get
        return _get()
    except ImportError:
        return "mycroft"


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_xdg_config_locations():
    # This includes both the user config and
    # /etc/xdg/mycroft/mycroft.conf
    xdg_paths = list(reversed(
        [join(p, get_config_filename())
         for p in get_xdg_config_dirs()]
    ))
    return xdg_paths


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_xdg_data_dirs():
    try:
        from ovos_config.locations import get_xdg_data_dirs as _get
        return _get()
    except ImportError:
        return [expanduser("~/.local/share/mycroft")]


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_xdg_config_dirs(folder=None):
    try:
        from ovos_config.locations import get_xdg_config_dirs as _get
        return _get()
    except ImportError:
        folder = folder or get_xdg_base()
        xdg_dirs = xdg.xdg_config_dirs() + [xdg.xdg_config_home()]
        return [join(path, folder) for path in xdg_dirs]


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_xdg_cache_save_path(folder=None):
    try:
        from ovos_config.locations import get_xdg_cache_save_path as _get
        return _get()
    except ImportError:
        folder = folder or get_xdg_base()
        return join(xdg.xdg_cache_home(), folder)


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_xdg_data_save_path():
    try:
        from ovos_config.locations import get_xdg_data_save_path as _get
        return _get()
    except ImportError:
        return expanduser("~/.local/share/mycroft")


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_xdg_config_save_path():
    try:
        from ovos_config.locations import get_xdg_config_save_path as _get
        return _get()
    except ImportError:
        return expanduser("~/.config/mycroft")


@deprecated("XDG is always used.", "0.1.0")
def is_using_xdg():
    """ DEPRECATED """
    return True


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def set_xdg_base(*args, **kwargs):
    try:
        from ovos_config.meta import set_xdg_base as _set
        _set(*args, **kwargs)
    except:
        pass


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def set_config_filename(*args, **kwargs):
    try:
        from ovos_config.meta import config_filename as _set
        _set(*args, **kwargs)
    except:
        pass


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_config_filename():
    try:
        from ovos_config.locale import get_config_filename as _get
        return _get()
    except ImportError:
        return "mycroft.conf"


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def get_ovos_default_config_paths():
    try:
        from ovos_config.meta import get_ovos_default_config_paths as _get
        return _get()
    except:
        return ["/etc/OpenVoiceOS/ovos.conf"]


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def read_mycroft_config():
    try:
        from ovos_config import Configuration
        return Configuration()
    except ImportError:
        pass
    path = expanduser(f"~/.config/mycroft/mycroft.conf")
    if isfile(path):
        with open(path) as f:
            return json.load(f)
    return {
        # TODO - default cfg
        "lang": "en-us"
    }


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def update_mycroft_config(config, path=None, bus=None):
    try:
        from ovos_config.config import update_mycroft_config as _update
        _update(config, path, bus)
    except ImportError:
        pass
    # save in default user location
    path = expanduser(f"~/.config/mycroft")
    makedirs(path, exist_ok=True)
    with open(f"{path}/mycroft.conf", "w") as f:
        json.dump(config, f, indent=2)


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def set_default_config(*args, **kwargs):
    try:
        from ovos_config.meta import set_default_config as _set
        _set(*args, **kwargs)
    except:
        pass


@deprecated("configuration moved to the `ovos_config` package.", "0.1.0")
def save_ovos_core_config(*args, **kwargs):
    try:
        from ovos_config.meta import save_ovos_config as _set
        _set(*args, **kwargs)
    except:
        pass


try:
    from ovos_config.models import (
        LocalConf,
        ReadOnlyConfig,
        MycroftUserConfig,
        MycroftDefaultConfig,
        MycroftSystemConfig,
        MycroftXDGConfig
    )
except ImportError:
    LOG.warning("configuration classes moved to the `ovos_config.models` package. "
                "This submodule will be removed in ovos_utils 0.1.0")
    from combo_lock import NamedLock
    import yaml
    from ovos_utils.json_helper import load_commented_json, merge_dict


    class LocalConf(dict):
        """Config dictionary from file."""
        allow_overwrite = True
        # lock is shared among all subclasses,
        # regardless of what file is being edited only one file should change at a time
        # this ensure orderly behaviour in anything monitoring changes,
        #   eg FileWatcher util, configuration.patch bus handlers
        __lock = NamedLock("ovos_config")

        def __init__(self, path):
            super().__init__(self)
            self.path = path
            if path:
                self.load_local(path)

        def _get_file_format(self, path=None):
            """The config file format
            supported file extensions:
            - json (.json)
            - commented json (.conf)
            - yaml (.yaml/.yml)

            returns "yaml" or "json"
            """
            path = path or self.path
            if not path:
                return "dict"
            if path.endswith(".yml") or path.endswith(".yaml"):
                return "yaml"
            else:
                return "json"

        def load_local(self, path=None):
            """Load local json file into self.

            Args:
                path (str): file to load
            """
            path = path or self.path
            if not path:
                LOG.error(f"in memory configuration, nothing to load")
                return
            if exists(path) and isfile(path):
                with self.__lock:
                    try:
                        if self._get_file_format(path) == "yaml":
                            with open(path) as f:
                                config = yaml.safe_load(f)
                        else:
                            config = load_commented_json(path)
                        if config:
                            for key in config:
                                self.__setitem__(key, config[key])
                            LOG.debug(f"Configuration {path} loaded")
                        else:
                            LOG.debug(f"Empty config found at: {path}")
                    except Exception as e:
                        LOG.exception(f"Error loading configuration '{path}'")
            else:
                LOG.debug(f"Configuration '{path}' not defined, skipping")

        def reload(self):
            self.load_local(self.path)

        def store(self, path=None):
            path = path or self.path
            if not path:
                LOG.error(f"in memory configuration, no save location")
                return
            with self.__lock:
                if self._get_file_format(path) == "yaml":
                    with open(path, 'w+') as f:
                        yaml.dump(dict(self), f, allow_unicode=True,
                                  default_flow_style=False, sort_keys=False)
                else:
                    with open(path, 'w+') as f:
                        json.dump(self, f, indent=2)

        def merge(self, conf):
            merge_dict(self, conf)


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
                raise PermissionError(f"{self.path} is read only! it can not be modified at runtime")
            super().__setitem__(key, value)

        def merge(self, *args, **kwargs):
            if not self.allow_overwrite:
                raise PermissionError(f"{self.path} is read only! it can not be modified at runtime")
            super().merge(*args, **kwargs)

        def store(self, path=None):
            if not self.allow_overwrite:
                raise PermissionError(f"{self.path} is read only! it can not be modified at runtime")
            super().store(path)


    class MycroftDefaultConfig(ReadOnlyConfig):
        def __init__(self):
            super().__init__(join(get_xdg_config_save_path(), get_config_filename()))

        def set_root_config_path(self, root_config):
            # in case we got it wrong / non standard
            self.path = root_config
            self.reload()


    class MycroftSystemConfig(ReadOnlyConfig):
        def __init__(self, allow_overwrite=False):
            super().__init__("/etc/mycroft/mycroft.conf", allow_overwrite)


    class RemoteConf(LocalConf):
        def __init__(self, cache=get_webcache_location()):
            super(RemoteConf, self).__init__(cache)


    MycroftXDGConfig = MycroftUserConfig = MycroftDefaultConfig
