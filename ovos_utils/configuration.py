from importlib.util import find_spec
from os.path import isfile, join, isdir

from json_database import JsonStorage

from ovos_utils.json_helper import load_commented_json, merge_dict
from ovos_utils.log import LOG
from ovos_utils.system import search_mycroft_core_location
from ovos_utils.xdg_utils import (
    xdg_config_home,
    xdg_config_dirs,
    xdg_data_home,
    xdg_data_dirs,
    xdg_cache_home
)


def get_xdg_config_dirs(folder=None):
    folder = folder or get_xdg_base()
    return [join(path, folder) for path in xdg_config_dirs() if isdir(join(path, folder))]


def get_xdg_data_dirs(folder=None):
    folder = folder or get_xdg_base()
    return [join(path, folder) for path in xdg_data_dirs() if isdir(join(path, folder))]


def get_xdg_config_save_path(folder=None):
    folder = folder or get_xdg_base()
    return join(xdg_config_home(), folder)


def get_xdg_data_save_path(folder=None):
    folder = folder or get_xdg_base()
    return join(xdg_data_home(), folder)


def get_xdg_cache_save_path(folder=None):
    folder = folder or get_xdg_base()
    return join(xdg_cache_home(), folder)


def get_ovos_config():
    config = {"xdg": True,
              "base_folder": "mycroft",
              "config_filename": "mycroft.conf",
              "default_config_path": find_default_config()}

    try:
        if isfile("/etc/OpenVoiceOS/ovos.conf"):
            config = merge_dict(config,
                                load_commented_json(
                                    "/etc/OpenVoiceOS/ovos.conf"))
        elif isfile("/etc/mycroft/ovos.conf"):
            config = merge_dict(config,
                                load_commented_json("/etc/mycroft/ovos.conf"))
    except:
        # tolerate bad json TODO proper exception (?)
        pass

    # This includes both the user config and
    # /etc/xdg/OpenVoiceOS/ovos.conf
    for p in get_xdg_config_dirs("OpenVoiceOS"):
        if isfile(join(p, "ovos.conf")):
            try:
                xdg_cfg = load_commented_json(join(p, "ovos.conf"))
                config = merge_dict(config, xdg_cfg)
            except:
                # tolerate bad json TODO proper exception (?)
                pass

    # let's check for derivatives specific configs
    # the assumption is that these cores are exclusive to each other,
    # this will never find more than one override
    # TODO this works if using dedicated .venvs what about system installs?
    cores = config.get("module_overrides") or {}
    for k in cores:
        if find_spec(k):
            config = merge_dict(config, cores[k])
            break
    else:
        subcores = config.get("submodule_mappings") or {}
        for k in subcores:
            if find_spec(k):
                config = merge_dict(config, cores[subcores[k]])
                break

    return config


def is_using_xdg():
    return get_ovos_config().get("xdg", True)


def get_xdg_base():
    return get_ovos_config().get("base_folder") or "mycroft"


def save_ovos_core_config(new_config):
    OVOS_CONFIG = join(get_xdg_config_save_path("OpenVoiceOS"),
                       "ovos.conf")
    cfg = JsonStorage(OVOS_CONFIG)
    cfg.update(new_config)
    cfg.store()
    return cfg


def set_xdg_base(folder_name):
    LOG.info(f"XDG base folder set to: '{folder_name}'")
    save_ovos_core_config({"base_folder": folder_name})


def set_config_filename(file_name, core_folder=None):
    if core_folder:
        set_xdg_base(core_folder)
    LOG.info(f"config filename set to: '{file_name}'")
    save_ovos_core_config({"config_filename": file_name})


def set_default_config(file_path=None):
    file_path = file_path or find_default_config()
    LOG.info(f"default config file changed to: {file_path}")
    save_ovos_core_config({"default_config_path": file_path})


def find_default_config():
    mycroft_root = search_mycroft_core_location()
    if not mycroft_root:
        raise FileNotFoundError("Couldn't find mycroft core root folder.")
    return join(mycroft_root, "mycroft", "configuration", "mycroft.conf")


def find_user_config():
    if is_using_xdg():
        path = join(get_xdg_config_save_path(), get_config_filename())
        if isfile(path):
            return path
    old, path = get_config_locations(default=False, web_cache=False,
                                     system=False, old_user=True,
                                     user=True)
    if isfile(path):
        return path
    if isfile(old):
        return old
    # mark1 runs as a different user
    sysconfig = MycroftSystemConfig()
    platform_str = sysconfig.get("enclosure", {}).get("platform", "")
    if platform_str == "mycroft_mark_1":
        path = "/home/mycroft/.mycroft/mycroft.conf"
    return path


def get_config_locations(default=True, web_cache=True, system=True,
                         old_user=True, user=True):
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
        if is_using_xdg():
            locs.append(f"{get_xdg_config_save_path()}/{ovos_cfg['config_filename']}")
        else:
            locs.append(f"~/.{ovos_cfg['base_folder']}/{ovos_cfg['config_filename']}")
    return locs


def get_webcache_location():
    return join(get_xdg_config_save_path(), 'web_cache.json')


def get_xdg_config_locations():
    # This includes both the user config and
    # /etc/xdg/mycroft/mycroft.conf
    xdg_paths = list(reversed(
        [join(p, get_config_filename())
         for p in get_xdg_config_dirs()]
    ))
    return xdg_paths


def get_config_filename():
    return get_ovos_config().get("config_filename") or "mycroft.conf"


def set_config_name(name, core_folder=None):
    # TODO deprecate, was only out in a couple versions
    # renamed to match HolmesV
    set_config_filename(name, core_folder)


def read_mycroft_config():
    conf = LocalConf("tmp/dummy.conf")
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


class LocalConf(JsonStorage):
    """
        Config dict from file.
    """
    allow_overwrite = True

    def __init__(self, path=None):
        super(LocalConf, self).__init__(path)


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

    def merge(self, *args, **kwargs):
        if not self.allow_overwrite:
            raise PermissionError
        super().merge(*args, **kwargs)

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
        path = get_ovos_config()["default_config_path"]
        super().__init__(path)
        if not self.path or not isfile(self.path):
            LOG.debug(f"mycroft root path not found, could not load default .conf: {self.path}")

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
