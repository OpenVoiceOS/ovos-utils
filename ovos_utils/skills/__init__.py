from ovos_utils.configuration import read_mycroft_config, update_mycroft_config
from ovos_utils.messagebus import wait_for_reply
from os.path import join, isdir
import xdg


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
    xdg_skills = xdg.BaseDirectory.save_data_path('mycroft/skills')
    if isdir(xdg_skills):
        return xdg_skills
    config = config or read_mycroft_config()
    # read user defined location
    if config:
        skill_folder = config["skills"]["msm"]["directory"]
        return join(config["data_dir"], skill_folder)
    # check if default path exists
    elif isdir("/opt/mycroft/skills"):
        return "/opt/mycroft/skills"

    # .conf not found, xdg directory not detected, default path not
    # detected, doesn't look like we are running mycroft-core
    return None
