from datetime import datetime
from dateutil.tz import gettz, tzlocal
from typing import Any

# used to calculate timespans
DAYS_IN_1_YEAR = 365.2425
DAYS_IN_1_MONTH = 30.42


def get_config_tz() -> Any:
    """Get the configured timezone or, if missing, defaults to local timezone

    Returns:
        Any: timezone
    """
    try:
        from ovos_config.locale import get_config_tz as _get_config_tz
        return _get_config_tz()
    except ImportError:
        return tzlocal()


def now_utc() -> datetime:
    """ Retrieve the current time in UTC

    Returns:
        (datetime): The current time in Universal Time, aka GMT
    """
    return datetime.utcnow().replace(tzinfo=gettz("UTC"))


def now_local(tz: datetime.tzinfo = None) -> datetime:
    """ Retrieve the current time

    Args:
        tz (datetime.tzinfo, optional): Timezone, default to user's settings

    Returns:
        (datetime): The current time
    """
    tz = tz or get_config_tz()
    return datetime.now(tz)


def to_utc(dt: datetime) -> datetime:
    """ Convert a datetime with timezone info to a UTC datetime

    Args:
        dt (datetime): A datetime (presumably in some local zone)
    Returns:
        (datetime): time converted to UTC
    """
    tz = gettz("UTC")
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=get_config_tz())
    return dt.astimezone(tz)


def to_local(dt: datetime) -> datetime:
    """ Convert a datetime to the user's local timezone

    Args:
        dt (datetime): A datetime (if no timezone, defaults to UTC)
    Returns:
        (datetime): time converted to the local timezone
    """
    tz = get_config_tz()
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=get_config_tz())
    return dt.astimezone(tz)


def to_system(dt: datetime) -> datetime:
    """Convert a datetime to the system's local timezone

    Args:
        dt (datetime): A datetime (if no timezone, assumed to be UTC)
    Returns:
        (datetime): time converted to the operation system's timezone
    """
    tz = tzlocal()
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=get_config_tz())
    return dt.astimezone(tz)


def is_leap_year(year: int) -> bool:
    """Checks if input year is a leap year

    Args:
        year (int): the year to check
    Returns:
        bool: if the input is an leap year
    """
    return (year % 400 == 0) or ((year % 4 == 0) and (year % 100 != 0))


def get_next_leap_year(year: int) -> int:
    """Get the following leap year of a reference year 

    Args:
        year (int): reference year

    Returns:
        int: following leap year
    """
    next_year = year + 1
    if is_leap_year(next_year):
        return next_year
    else:
        return get_next_leap_year(next_year)
