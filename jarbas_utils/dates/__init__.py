from lingua_franca.lang.parse_en import extract_duration_en, \
    _convert_words_to_numbers_en, is_numeric, normalize_en
from lingua_franca.lang.common_data_en import _ORDINAL_BASE_EN
from lingua_franca.time import now_local
from lingua_franca.lang import get_primary_lang_code
from datetime import timedelta, datetime, date, time
from jarbas_utils.dates.seasons import Hemisphere, HEMISPHERES_EN, get_season_range
from enum import Enum

WEEKDAY_EN = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday"
}

MONTH_EN = {
    1: "january",
    2: "february",
    3: "march",
    4: "april",
    5: "may",
    6: "june",
    7: "july",
    8: "august",
    9: "september",
    10: "october",
    11: "november",
    12: "december"
}

WEEKDAY_SHORT_EN = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun"
}

MONTH_SHORT_EN = {
    1: "jan",
    2: "feb",
    3: "mar",
    4: "apr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "aug",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dec"
}


class TimeResolution(Enum):
    SECOND = 0
    MINUTE = 1
    HOUR = 2


class DateResolution(Enum):
    DAY_OF_MONTH = 0
    WEEK_OF_MONTH = 1
    MONTH_OF_YEAR = 2
    YEAR = 3
    DECADE = 4
    CENTURY = 5
    MILLENNIUM = 6
    WEEK_OF_YEAR = 7
    DAY_OF_YEAR = 8
    MONTH_OF_CENTURY = 9
    MONTH_OF_DECADE = 10
    MONTH_OF_MILLENIUM = 11
    DAY_OF_DECADE = 12
    DAY_OF_CENTURY = 13
    DAY_OF_MILLENIUM = 14
    DECADE_OF_CENTURY = 15
    DECADE_OF_MILLENIUM = 16
    CENTURY_OF_MILLENIUM = 17
    YEAR_OF_DECADE = 18
    YEAR_OF_CENTURY = 19
    YEAR_OF_MILLENIUM = 20
    WEEK_OF_CENTURY = 21
    WEEK_OF_DECADE = 22
    WEEK_OF_MILLENIUM = 23
    DAY = 24
    MONTH = 25
    WEEK = 26
    WEEKEND = 27
    WEEKEND_OF_MONTH = 28
    WEEKEND_OF_YEAR = 29
    WEEKEND_OF_DECADE = 30
    WEEKEND_OF_CENTURY = 31
    WEEKEND_OF_MILLENNIUM = 32


def _tokenize_en(date_string):
    date_string = _convert_words_to_numbers_en(date_string, ordinals=True)
    date_string = date_string \
        .replace("a day", "1 day").replace("a month", "1 month") \
        .replace("a week", "1 week").replace("a year", "1 year") \
        .replace("a century", "1 century").replace("a decade", "1 decade")
    words = date_string.split()
    cleaned = ""
    for idx, word in enumerate(words):
        if word == "-":
            word = "minus"
            words[idx] = word
        elif word == "+":
            word = "plus"
            words[idx] = word
        elif word[0] == "-" and word[1].isdigit():
            cleaned += " minus " + word[1:].rstrip(",.!?;:-)/]=}")
        elif word[0] == "+" and word[1].isdigit():
            cleaned += " plus " + word[1:].rstrip(",.!?;:-)/]=}")
        else:
            cleaned += " " + word.rstrip(",.!?;:-)/]=}")\
                .lstrip(",.!?;:-(/[={")
    for n, ordinal in _ORDINAL_BASE_EN.items():
        cleaned = cleaned.replace(ordinal, str(n))
    cleaned = normalize_en(cleaned, remove_articles=True)
    return cleaned.split()


def int_to_month(month, lang=None):
    lang_code = get_primary_lang_code(lang)
    if lang_code.startswith("en"):
        return MONTH_EN[month]
    return str(month)


def int_to_weekday(weekday, lang=None):
    lang_code = get_primary_lang_code(lang)
    if lang_code.startswith("en"):
        return WEEKDAY_EN[weekday]
    return str(weekday)


def month_to_int(month, lang=None):
    if isinstance(month, int) or isinstance(month, float):
        return int(month)
    lang_code = get_primary_lang_code(lang)
    inv_map = {}
    if lang_code.startswith("en"):
        inv_map = {v: k for k, v in MONTH_SHORT_EN.items()}
    for short in inv_map:
        if month.startswith(short):
            return inv_map[short]
    return None


def weekday_to_int(weekday, lang=None):
    if isinstance(weekday, int) or isinstance(weekday, float):
        return int(weekday)
    lang_code = get_primary_lang_code(lang)
    inv_map = {}
    if lang_code.startswith("en"):
        inv_map = {v: k for k, v in WEEKDAY_SHORT_EN.items()}

    for short in inv_map:
        if weekday.startswith(short):
            return inv_map[short]
    return None


def get_week_range(ref_date):
    start = ref_date - timedelta(days=ref_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_weekend_range(ref_date):
    if ref_date.weekday() < 5:
        start, end = get_week_range(ref_date)
        start = start + timedelta(days=5)
    elif ref_date.weekday() == 5:
        start = ref_date
    elif ref_date.weekday() == 6:
        start = ref_date - timedelta(days=1)
    return start, start + timedelta(days=1)


def get_month_range(ref_date):
    start = ref_date.replace(day=1)
    end = ref_date.replace(day=1, month=ref_date.month + 1) - timedelta(days=1)
    return start, end


def get_year_range(ref_date):
    start = ref_date.replace(day=1, month=1)
    end = ref_date.replace(day=31, month=12)
    return start, end


def get_decade_range(ref_date):
    start = date(day=1, month=1, year=(ref_date.year // 10)*10)
    end = date(day=31, month=12, year=start.year + 9)
    return start, end


def get_century_range(ref_date):
    start = date(day=1, month=1, year=(ref_date.year // 100) * 100)
    end = date(day=31, month=12, year=start.year + 99)
    return start, end


def get_millennium_range(ref_date):
    start = date(day=1, month=1, year=(ref_date.year // 1000) * 1000)
    end = date(day=31, month=12, year=start.year + 999)
    return start, end


def get_ordinal(ordinal, ref_date=None,
                resolution=DateResolution.DAY_OF_MONTH):
    ordinal = int(ordinal)
    ref_date = ref_date or now_local()
    if isinstance(ref_date, datetime):
        ref_date = ref_date.date()

    _decade = (ref_date.year // 10) * 10 or 1
    _century = (ref_date.year // 100) * 100 or 1
    _mil = (ref_date.year // 1000) * 1000 or 1

    print(resolution)
    if resolution == DateResolution.DAY:
        if ordinal < 0:
            raise OverflowError("The last day of existence can not be "
                                "represented")
        ordinal -= 1
        return date(year=1, day=1, month=1) + timedelta(days=ordinal)
    if resolution == DateResolution.DAY_OF_MONTH:
        if ordinal == -1:
            # last day
            if ref_date.month + 1 == 13:
                return ref_date.replace(day=31, month=12)
            return ref_date.replace(month=ref_date.month + 1, day=1) - \
                   timedelta(days=1)
        return ref_date.replace(day=ordinal)
    if resolution == DateResolution.DAY_OF_YEAR:
        if ordinal == -1:
            # last day
            return date(year=ref_date.year, day=31, month=12)
        ordinal -= 1
        return date(year=ref_date.year, day=1, month=1) + \
               timedelta(days=ordinal)
    if resolution == DateResolution.DAY_OF_DECADE:
        if ordinal == -1:
            # last day
            if _decade + 10 == 10000:
                return date(year=9999, day=31, month=12)
            return date(year=_decade + 10, day=1, month=1) - timedelta(1)
        ordinal -= 1
        return date(year=_decade, day=1, month=1) + timedelta(days=ordinal)

    if resolution == DateResolution.DAY_OF_CENTURY:
        if ordinal == -1:
            # last day
            if _century + 100 == 10000:
                return date(year=9999, day=31, month=12)
            return date(year=_century + 100, day=1, month=1) - timedelta(1)

        return datetime(year=_century, day=1, month=1).date() + timedelta(days=ordinal - 1)

    if resolution == DateResolution.DAY_OF_MILLENIUM:
        if ordinal == -1:
            # last day
            if _mil + 1000 == 10000:
                return date(year=9999, day=31, month=12)
            return date(year=_mil + 1000, day=1, month=1) - timedelta(1)
        return date(year=_mil, day=1, month=1) + timedelta(days=ordinal - 1)

    if resolution == DateResolution.WEEK:
        if ordinal < 0:
            raise OverflowError("The last week of existence can not be "
                                "represented")
        return date(year=1, day=1, month=1) + timedelta(weeks=ordinal)
    if resolution == DateResolution.WEEK_OF_MONTH:
        if ordinal == -1:
            _start, _end = get_week_range(ref_date.replace(day=28))
            return _start
        _start, _end = get_week_range(
            ref_date.replace(day=1) + timedelta(weeks=ordinal - 1))
        return _start
    if resolution == DateResolution.WEEK_OF_YEAR:
        if ordinal == -1:
            _start, _end = get_week_range(ref_date.replace(day=31, month=12))
            return _start
        return ref_date.replace(day=1, month=1) + timedelta(weeks=ordinal - 1)

    if resolution == DateResolution.WEEK_OF_DECADE:
        if ordinal == -1:
            _start, _end = get_week_range(date(day=31, month=12,
                                               year=_decade + 9))
            return _start
        if ordinal == 1:
            return date(day=1, month=1, year=_decade)
        ordinal -= 1
        return date(day=1, month=1, year=_decade) + timedelta(weeks=ordinal)
    if resolution == DateResolution.WEEK_OF_CENTURY:
        if ordinal == -1:
            _start, _end = get_week_range(date(day=31, month=12,
                                               year=_century + 99))
            return _start
        if ordinal == 1:
            return date(day=1, month=1, year=_century)
        ordinal -= 1
        return date(day=1, month=1, year=_century) + timedelta(weeks=ordinal)
    if resolution == DateResolution.WEEK_OF_MILLENIUM:
        if ordinal == -1:
            _start, _end = get_week_range(date(day=31, month=12,
                                               year=_mil + 999))
            return _start
        if ordinal == 1:
            return date(day=1, month=1, year=_mil)
        ordinal -= 1
        return date(day=1, month=1, year=_mil) + timedelta(weeks=ordinal)

    if resolution == DateResolution.MONTH:
        if ordinal < 0:
            raise OverflowError("The last month of existence can not be "
                                "represented")
        return date(year=1, day=1, month=1) + timedelta(weeks=ordinal * 4)
    if resolution == DateResolution.MONTH_OF_YEAR:
        if ordinal == -1:
            return ref_date.replace(month=12, day=1)
        return ref_date.replace(month=ordinal, day=1)
    if resolution == DateResolution.MONTH_OF_CENTURY:
        if ordinal == -1:
            return date(year=_century + 99, day=1, month=12)
        _date = ref_date.replace(month=1, day=1, year=_century)
        _date += ordinal * timedelta(weeks=4)
        return _date - timedelta(days=1)
    if resolution == DateResolution.MONTH_OF_DECADE:
        if ordinal == -1:
            return date(year=_decade + 9, day=1, month=12)
        _date = ref_date.replace(month=1, day=1, year=_decade)
        _date += ordinal * timedelta(weeks=4)
        return _date - timedelta(days=1)
    if resolution == DateResolution.MONTH_OF_MILLENIUM:
        if ordinal == -1:
            return date(year=_mil + 999, day=1, month=12)
        _date = ref_date.replace(month=1, day=1, year=_mil)
        _date += ordinal * timedelta(weeks=4)
        return _date - timedelta(days=1)

    if ordinal == 0:
        # NOTE: no year 0
        return date(year=1, day=1, month=1)

    if resolution == DateResolution.YEAR:
        if ordinal == -1:
            raise OverflowError("The last year of existence can not be "
                                "represented")
        return date(year=ordinal, day=1, month=1)
    if resolution == DateResolution.YEAR_OF_DECADE:
        if ordinal == -1:
            return date(year=_decade + 9, day=31, month=12)
        assert 0 < ordinal < 10
        return date(year=_decade + ordinal, day=1, month=1)
    if resolution == DateResolution.YEAR_OF_CENTURY:
        if ordinal == -1:
            return date(year=_century - 1, day=31, month=12)
        return date(year=_century + ordinal, day=1, month=1)
    if resolution == DateResolution.YEAR_OF_MILLENIUM:
        if ordinal == -1:
            return date(year=_mil - 1, day=31, month=12)
        return date(year=_mil + ordinal, day=1, month=1)
    if resolution == DateResolution.DECADE:
        if ordinal == -1:
            raise OverflowError("The last decade of existence can not be "
                                "represented")
        if ordinal == 1:
            return date(day=1, month=1, year=1)
        ordinal -= 1
        return date(year=ordinal * 10, day=1, month=1)
    if resolution == DateResolution.DECADE_OF_CENTURY:
        if ordinal == -1:
            return date(year=_century + 90, day=1, month=1)

        assert 0 < ordinal < 10

        if ordinal == 1:
            return date(day=1, month=1, year=_century)
        ordinal -= 1

        return date(year=_century + ordinal * 10, day=1, month=1)
    if resolution == DateResolution.DECADE_OF_MILLENIUM:
        if ordinal == -1:
            return date(year=_mil + 990, day=1, month=1)

        assert 0 < ordinal < 1000

        if ordinal == 1:
            return date(day=1, month=1, year=_mil)
        ordinal -= 1
        return date(year=_mil + ordinal * 10,  day=1, month=1)
    if resolution == DateResolution.CENTURY:
        if ordinal == -1:
            raise OverflowError("The last century of existence can not be "
                                "represented")
        return date(year=ordinal * 100, day=1, month=1)
    if resolution == DateResolution.CENTURY_OF_MILLENIUM:
        if ordinal == -1:
            return date(year=_mil + 900, day=1, month=1)

        assert 0 < ordinal < 100

        if ordinal == 1:
            return date(day=1, month=1, year=_mil)
        ordinal -= 1
        return date(year=_mil + ordinal * 100,  day=1, month=1)
    if resolution == DateResolution.MILLENNIUM:
        if ordinal < 0:
            raise OverflowError("The last millennium of existence can not be "
                                "represented")
        if ordinal == 1:
            return date(day=1, month=1, year=1)
        return date(year=ordinal * 1000, day=1, month=1)
    raise ValueError


if __name__ == "__main__":

    ref_date = date(day=12, month=7, year=3124)

    def test_ranges():
        start, end = get_week_range(ref_date)
        assert start == ref_date - timedelta(days=ref_date.weekday())
        assert end == start + timedelta(days=6)

        start, end = get_month_range(ref_date)
        assert start == ref_date.replace(day=1)
        assert end == ref_date.replace(day=31)

        start, end = get_season_range(ref_date)
        assert start == ref_date.replace(day=21, month=6)
        assert end == ref_date.replace(day=21, month=9)

        start, end = get_year_range(ref_date)
        assert start == ref_date.replace(day=1, month=1)
        assert end == ref_date.replace(day=31, month=12)

        start, end = get_decade_range(ref_date)
        assert start == date(day=1, month=1, year=3120)
        assert end == date(day=31, month=12, year=3129)

        start, end = get_century_range(ref_date)
        assert start == date(day=1, month=1, year=3100)
        assert end == date(day=31, month=12, year=3199)

        start, end = get_millennium_range(ref_date)
        assert start == date(day=1, month=1, year=3000)
        assert end == date(day=31, month=12, year=3999)

        # current or next weekend
        start, end = get_weekend_range(ref_date)
        assert start == ref_date
        assert end == start + timedelta(days=1)

        start, end = get_weekend_range(ref_date + timedelta(days=1))
        assert start == ref_date

        start, end = get_weekend_range(ref_date + timedelta(days=2))
        assert start == ref_date + timedelta(days=7)

    test_ranges()