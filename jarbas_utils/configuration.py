from jarbas_utils.log import LOG
from jarbas_utils.json_helper import merge_dict, load_commented_json
from os.path import isfile, exists, expanduser, join, dirname, isdir
from os import makedirs
import json

MYCROFT_SYSTEM_CONFIG = "/etc/mycroft/mycroft.conf"
MYCROFT_USER_CONFIG = join(expanduser("~"), ".mycroft", "mycroft.conf")


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
        super().__init__(MYCROFT_USER_CONFIG)


class MycroftDefaultConfig(ReadOnlyConfig):
    def __init__(self):
        path = None
        # TODO check system config platform and go directly to correct path if it exists
        paths = [
            "/opt/venvs/mycroft-core/lib/python3.7/site-packages/",  # mark1/2
            "/opt/venvs/mycroft-core/lib/python3.4/site-packages/ ",  # old mark1 installs
            "/home/pi/mycroft-core"  # picroft
        ]
        for p in paths:
            p = join(p, "mycroft", "configuration", "mycroft.conf")
            if isfile(p):
                path = p
        super().__init__(path)
        if not self.path or not isfile(self.path):
            LOG.warning("mycroft root path not found")

    def set_mycroft_root(self, mycroft_root_path):
        self.path = join(mycroft_root_path, "mycroft", "configuration", "mycroft.conf")
        self.reload()


class MycroftSystemConfig(ReadOnlyConfig):
    def __init__(self, allow_overwrite=False):
        super().__init__(MYCROFT_SYSTEM_CONFIG, allow_overwrite)


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
