from ovos_utils.system import search_mycroft_core_location, is_running_from_module
from ovos_utils.xdg_utils import (
    xdg_config_home,
    xdg_config_dirs,
    xdg_data_home,
    xdg_data_dirs,
    xdg_cache_home
)
from os.path import expanduser, isfile
from os import makedirs
import json


# if ovos-config not installed, these methods are still needed internally

def get_xdg_base():
    try:
        from ovos_config.meta import get_xdg_base as _get
        return _get()
    except ImportError:
        return "mycroft"


def get_xdg_data_save_path():
    try:
        from ovos_config.locations import get_xdg_data_save_path as _get
        return _get()
    except ImportError:
        return expanduser("~/.local/share/mycroft")


def get_xdg_data_dirs():
    try:
        from ovos_config.locations import get_xdg_data_dirs as _get
        return _get()
    except ImportError:
        return [expanduser("~/.local/share/mycroft")]


def get_default_lang():
    try:
        from ovos_config.locale import get_default_lang as _get
        return _get()
    except ImportError:
        return read_mycroft_config().get("lang", "en-us")


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


# ovos-config not installed, optional compat imports below don't matter
try:
    from ovos_config.locations import (
        get_xdg_config_dirs,
        get_xdg_config_save_path,
        get_xdg_cache_save_path,
        find_default_config,
        find_user_config,
        get_config_locations,
        get_webcache_location,
        get_xdg_config_locations)
    from ovos_config.meta import (
        get_ovos_config,
        get_ovos_default_config_paths,
        is_using_xdg,
        set_xdg_base,
        set_config_filename,
        set_default_config,
        get_config_filename
    )
    from ovos_config.models import (
        LocalConf,
        ReadOnlyConfig,
        MycroftUserConfig,
        MycroftDefaultConfig,
        MycroftSystemConfig,
        MycroftXDGConfig
    )
    from ovos_config.meta import save_ovos_config as save_ovos_core_config
except ImportError:
    from ovos_utils.log import LOG

    LOG.warning("configuration moved to the `ovos_config` package. This submodule "
                "will be removed in ovos_utils 0.1.0")
