from ovos_utils.configuration import read_mycroft_config, update_mycroft_config
from os.path import join


def blacklist_skill(skill):
    skills_config = read_mycroft_config().get("skills", {})
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


def whitelist_skill(skill):
    skills_config = read_mycroft_config().get("skills", {})
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


def make_priority_skill(skill):
    skills_config = read_mycroft_config().get("skills", {})
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


def get_skills_folder():
    config = read_mycroft_config()
    data_dir = config["data_dir"]
    skill_folder = config["skills"]["msm"]["directory"]
    return join(data_dir, skill_folder)
