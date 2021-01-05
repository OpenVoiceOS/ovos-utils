from ovos_utils.log import LOG
from ovos_utils.enclosure import detect_enclosure
from ovos_utils.enclosure import MycroftEnclosures
from ovos_utils.json_helper import merge_dict, load_commented_json
from ovos_utils.system import search_mycroft_core_location
from os.path import isfile, exists, expanduser, join, dirname, isdir
from os import makedirs
import json

MYCROFT_SYSTEM_CONFIG = "/etc/mycroft/mycroft.conf"
MYCROFT_USER_CONFIG = join(expanduser("~"), ".mycroft", "mycroft.conf")


def get_config_fingerprint():
    conf = read_mycroft_config()
    listener_conf = conf.get("listener", {})
    skills_conf = conf.get("skills", {})
    return {
        "enclosure": conf.get("enclosure", {}).get("platform"),
        "data_dir": conf.get("data_dir"),
        "msm_skills_dir": skills_conf.get("msm", {}).get("directory"),
        "ipc_path": conf.get("ipc_path"),
        "input_device_name": listener_conf.get("device_name"),
        "input_device_index": listener_conf.get("device_index"),
        "default_audio_backend": conf.get("Audio", {}).get("default-backend"),
        "priority_skills": skills_conf.get("priority_skills"),
        "backend_url": conf.get("server", {}).get("url")
    }


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


# TODO use json_database.JsonStorage
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

                LOG.debug("Configuration {} loaded".format(path))
            except Exception as e:
                LOG.error("Error loading configuration '{}'".format(path))
                LOG.error(repr(e))
        else:
            LOG.debug("Configuration '{}' not defined, skipping".format(path))

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
        path = MYCROFT_USER_CONFIG
        enclosure = detect_enclosure()
        if enclosure == MycroftEnclosures.MARK1 or \
                enclosure == MycroftEnclosures.OLD_MARK1:
            path = "/home/mycroft/.mycroft/mycroft.conf"
        super().__init__(path)


class MycroftDefaultConfig(ReadOnlyConfig):
    def __init__(self):
        mycroft_root = search_mycroft_core_location()
        if not mycroft_root:
            raise FileNotFoundError("Couldn't find mycroft core root folder.")
        path = join(mycroft_root, "mycroft",
                    "configuration", "mycroft.conf")
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
        super().__init__(MYCROFT_SYSTEM_CONFIG, allow_overwrite)



