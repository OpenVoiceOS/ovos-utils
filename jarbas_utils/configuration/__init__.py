from jarbas_utils.log import LOG
from os.path import isfile, exists, expanduser, join, dirname, isdir
from os import makedirs
import json

MYCROFT_SYSTEM_CONFIG = "/etc/mycroft/mycroft.conf"
MYCROFT_USER_CONFIG = join(expanduser("~"), ".mycroft", "mycroft.conf")


def merge_dict(base, delta):
    """
        Recursively merging configuration dictionaries.

        Args:
            base:  Target for merge
            delta: Dictionary to merge into base
    """

    for k, dv in delta.items():
        bv = base.get(k)
        if isinstance(dv, dict) and isinstance(bv, dict):
            merge_dict(bv, dv)
        else:
            base[k] = dv


def load_commented_json(filename):
    """ Loads an JSON file, ignoring comments

    Supports a trivial extension to the JSON file format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.

    NOTE: A file created with these style comments will break strict JSON
          parsers.  This is similar to but lighter-weight than "human json"
          proposed at https://hjson.org

    Args:
        filename (str):  path to the commented JSON file

    Returns:
        obj: decoded Python object
    """
    with open(filename) as f:
        contents = f.read()

    return json.loads(uncomment_json(contents))


def uncomment_json(commented_json_str):
    """ Removes comments from a JSON string.

    Supporting a trivial extension to the JSON format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.

    Example...
       {
         // comment
         'name' : 'value'
       }

    Args:
        commented_json_str (str):  a JSON string

    Returns:
        str: uncommented, legal JSON
    """
    lines = commented_json_str.splitlines()
    # remove all comment lines, starting with // or #
    nocomment = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        nocomment.append(line)

    return " ".join(nocomment)


class LocalConf(dict):
    """
        Config dict from file.
    """

    def __init__(self, path):
        super(LocalConf, self).__init__()
        if path:
            self.path = path
            self.load_local(path)

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
        self.allow_overwrite = True
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
    conf.merge(MycroftDefaultConfig)
    conf.merge(MycroftSystemConfig)
    conf.merge(MycroftUserConfig)
    return conf


def update_mycroft_config(config, path=None):
    if path is None:
        conf = MycroftUserConfig()
    else:
        conf = LocalConf(path)
    conf.merge(config)
    conf.store()
    return conf
