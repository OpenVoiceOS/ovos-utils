from ovos_bus_client.util import wait_for_reply


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


def skills_loaded(bus=None) -> bool:
    """
    Await a reply from mycroft.skills.all_loaded to check if all skills are
    loaded.
    @param bus: OVOS messagebus client
    @return: Are all skills loaded? True/False
    """
    if bus is None:
        return False
    reply = wait_for_reply('mycroft.skills.all_loaded',
                           'mycroft.skills.all_loaded.response',
                           bus=bus)
    if reply:
        return reply.data['status']
    return False
