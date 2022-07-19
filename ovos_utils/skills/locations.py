from os.path import join, isdir, dirname, expanduser, isfile
from os import makedirs, listdir
from typing import List, Optional
from ovos_config.locations import get_xdg_data_save_path, get_xdg_data_dirs
from ovos_config.config import Configuration
from ovos_utils.log import LOG


def get_installed_skill_ids(config=None) -> List[str]:
    """
    Gets a list of `skill_id`s for all installed skills
    @param config:
    @return:
    """
    skill_ids = get_plugin_skill_dirs()
    for d in get_skill_directories(config):
        for skill_dir in listdir(d):
            if isdir(skill_dir) and isfile(join(d, skill_dir, "__init__.py")):
                skill_ids.append(skill_dir)
    return skill_ids


def get_skill_directories(config=None) -> List[str]:
    """ returns list of skill directories ordered by expected loading order
    This corresponds to:
    - XDG_DATA_DIRS
    - default directory (see get_default_skills_directory method for details)
    - user defined extra directories
    Each directory contains individual skill folders to be loaded
    If a skill exists in more than one directory (same folder name) previous instances will be ignored
        ie. directories at the end of the list have priority over earlier directories
    NOTE: empty folders are interpreted as disabled skills
    new directories can be defined in mycroft.conf by specifying a full path
    each extra directory is expected to contain individual skill folders to be loaded
    the xdg folder name can also be changed, it defaults to "skills"
        eg. ~/.local/share/mycroft/FOLDER_NAME
    {
        "skills": {
            "directory": "skills",
            "extra_directories": ["path/to/extra/dir/to/scan/for/skills"]
        }
    }
    Args:
        conf (dict): mycroft.conf dict, will be loaded automatically if None
    """
    # the contents of each skills directory must be individual skill folders
    # we are still dependent on the mycroft-core structure of skill_id/__init__.py

    conf = config or Configuration()

    # load all valid XDG paths
    # NOTE: skills are actually code, but treated as user data!
    # they should be considered applets rather than full applications
    skill_locations = list(reversed(
        [join(p, "skills") for p in get_xdg_data_dirs()]
    ))

    # load the default skills folder
    # only meaningful if xdg support is disabled
    default = get_default_skills_directory(conf)
    if default not in skill_locations:
        skill_locations.append(default)

    # load additional explicitly configured directories
    conf = conf.get("skills") or {}
    # extra_directories is a list of directories containing skill subdirectories
    # NOT a list of individual skill folders
    skill_locations += conf.get("extra_directories") or []
    return skill_locations


def get_default_skills_directory(conf=None):
    """ return default directory to scan for skills
    This is only meaningful if xdg is disabled in ovos.conf
    If xdg is enabled then data_dir is always XDG_DATA_DIR
    If xdg is disabled then data_dir by default corresponds to /opt/mycroft
    users can define the data directory in mycroft.conf
    the skills folder name (relative to data_dir) can also be defined there
    NOTE: folder name also impacts all XDG skill directories!
    {
        "data_dir": "/opt/mycroft",
        "skills": {
            "directory": "skills"
        }
    }
    Args:
        conf (dict): mycroft.conf dict, will be loaded automatically if None
    """
    conf = conf or Configuration()
    path_override = conf["skills"].get("directory_override")

    # if .conf wants to use a specific path, use it!
    if path_override:
        LOG.warning("'directory_override' is deprecated!\n"
                    "It will no longer be supported after version 0.0.3\n"
                    "add the new path to 'extra_directories' instead")
        skills_folder = path_override
    elif conf["skills"].get("extra_directories") and \
            len(conf["skills"].get("extra_directories")) > 0:
        skills_folder = conf["skills"]["extra_directories"][0]
    else:
        skills_folder = join(get_xdg_data_save_path(), "skills")
    # create folder if needed
    try:
        makedirs(skills_folder, exist_ok=True)
    except PermissionError:  # old style /opt/mycroft/skills not available
        skills_folder = join(get_xdg_data_save_path(), "skills")
        makedirs(skills_folder, exist_ok=True)

    return expanduser(skills_folder)


def get_plugin_skill_dirs() -> list:
    import importlib.util
    from ovos_plugin_manager.skills import find_skill_plugins
    skill_dirs = list()
    plugins = find_skill_plugins()
    for skill_class in plugins.values():
        skill_dir = dirname(importlib.util.find_spec(
            skill_class.__module__).origin)
        skill_dirs.append(skill_dir)
    LOG.info(f"Located plugin skill_dirs: {skill_dirs}")
    return skill_dirs
