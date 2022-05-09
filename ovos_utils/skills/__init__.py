from ovos_utils.configuration import read_mycroft_config, update_mycroft_config, get_xdg_data_save_path
from ovos_utils.messagebus import wait_for_reply
from os.path import join, isdir, isfile
from os import listdir


def get_non_properties(obj):
    """Get attributes that are not properties from object.

    Will return members of object class along with bases down to MycroftSkill.

    Args:
        obj: object to scan

    Returns:
        Set of attributes that are not a property.
    """

    def check_class(cls):
        """Find all non-properties in a class."""
        # Current class
        d = cls.__dict__
        np = [k for k in d if not isinstance(d[k], property)]
        # Recurse through base classes excluding MycroftSkill and object
        for b in [b for b in cls.__bases__ if b.__name__ not in ("object", "MycroftSkill")]:
            np += check_class(b)
        return np

    return set(check_class(obj.__class__))


def skills_loaded(bus=None):
    reply = wait_for_reply('mycroft.skills.all_loaded',
                           'mycroft.skills.all_loaded.response',
                           bus=bus)
    if reply:
        return reply.data['status']
    return False


def blacklist_skill(skill, config=None):
    config = config or read_mycroft_config()
    skills_config = config.get("skills", {})
    blacklisted_skills = skills_config.get("blacklisted_skills", [])
    if skill not in blacklisted_skills:
        blacklisted_skills.append(skill)
        conf = {
            "skills": {
                "blacklisted_skills": blacklisted_skills
            }
        }
        update_mycroft_config(conf)
        return True
    return False


def whitelist_skill(skill, config=None):
    config = config or read_mycroft_config()
    skills_config = config.get("skills", {})
    blacklisted_skills = skills_config.get("blacklisted_skills", [])
    if skill in blacklisted_skills:
        blacklisted_skills.pop(skill)
        conf = {
            "skills": {
                "blacklisted_skills": blacklisted_skills
            }
        }
        update_mycroft_config(conf)
        return True
    return False


def make_priority_skill(skill, config=None):
    config = config or read_mycroft_config()
    skills_config = config.get("skills", {})
    priority_skills = skills_config.get("priority_skills", [])
    if skill not in priority_skills:
        priority_skills.append(skill)
        conf = {
            "skills": {
                "priority_skills": priority_skills
            }
        }
        update_mycroft_config(conf)
        return True
    return False


def get_skills_folder(config=None):
    # once XDG PR is merged skills folder will no longer be configurable,
    # skills are moved automatically to new locations
    # this is already live in mycroft-lib
    xdg_skills = join(get_xdg_data_save_path(), 'skills')
    if isdir(xdg_skills):
        return xdg_skills

    # read user defined location
    config = config or read_mycroft_config()
    if config:
        skill_folder = config["skills"]["msm"]["directory"]
        return join(config["data_dir"], skill_folder)

    # check if default path exists
    elif isdir("/opt/mycroft/skills"):
        return "/opt/mycroft/skills"

    # .conf not found, xdg directory not detected, default path not
    # detected, doesn't look like we are running mycroft-core
    return None


def get_installed_skills(config=None):
    skills_dir = get_skills_folder(config)
    installed_skills = []
    if skills_dir:
        for skill_id in listdir(skills_dir):
            skill_path = join(skills_dir, skill_id)
            if not isdir(skill_path):
                continue
            skill_file = join(skill_path, "__init__.py")
            if not isfile(skill_file):
                continue
            with open(skill_file) as f:
                if "def create_skill(" not in f.read():
                    continue
            installed_skills.append(skill_id)

    return installed_skills
