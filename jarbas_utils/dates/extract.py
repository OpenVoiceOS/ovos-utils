from lingua_franca.lang.parse_en import extract_duration_en, is_numeric
from lingua_franca.time import now_local
from datetime import timedelta, datetime, date, time
from jarbas_utils.dates import DateResolution, TimeResolution, _tokenize_en, \
    get_ordinal, get_week_range, get_century_range, get_decade_range, \
    get_millennium_range, get_month_range, get_year_range, get_weekend_range, \
    month_to_int, int_to_month, weekday_to_int, int_to_weekday
from jarbas_utils.dates.seasons import date_to_season, season_to_date, \
    get_season_range, Season, Hemisphere, SEASONS_EN, HEMISPHERES_EN, \
    next_season_date, last_season_date


def extract_time(time_str, default_time, sensitivity=TimeResolution.SECOND):
    time_qualifiers_am = ['morning']
    time_qualifiers_pm = ['afternoon', 'evening', 'night', 'tonight']
    markers = ['at', 'in', 'on', 'by', 'this', 'around', 'for', 'of', "within"]

    words = _tokenize_en(time_str)
    for idx, word in enumerate(words):
        if word == "":
            continue

        wordPrevPrev = words[idx - 2] if idx > 1 else ""
        wordPrev = words[idx - 1] if idx > 0 else ""
        wordNext = words[idx + 1] if idx + 1 < len(words) else ""
        wordNextNext = words[idx + 2] if idx + 2 < len(words) else ""
        word = word.rstrip('s')

    # TODO

    return None


def extract_date_en(date_str, ref_date,
                    resolution=DateResolution.DAY,
                    hemisphere=Hemisphere.NORTH):
    """ Convert a human date reference into an exact datetime

    Convert things like
        "today"
        "tomorrow"
        "next Tuesday"
        "August 3rd"
    into a date.  If a reference date is not provided, the current
    local time is used.  Also consumes the words used to define the date
    returning the remaining string.  For example, the string
       "what is Tuesday's weather forecast"
    returns the date for the forthcoming Tuesday relative to the reference
    date and the remainder string
       "what is weather forecast".

    The "next" instance of a day or weekend is considered to be no earlier than
    48 hours in the future. On Friday, "next Monday" would be in 3 days.
    On Saturday, "next Monday" would be in 9 days.

    Args:
        date_str(str): string containing date words
        ref_date (datetime): A reference date/time for "tommorrow", etc
        resolution (DateResolution): timedelta approximation

    Returns:
        [date, str]: An array containing the datetime and the remaining
                         text not consumed in the parsing, or None if no
                         date or time related text was found.
    """
    past_qualifiers = ["ago"]
    relative_qualifiers = ["from", "after"]
    relative_past_qualifiers = ["before"]
    of_qualifiers = [
        "of"]  # {ORDINAL} day/week/month.... of month/year/century..
    set_qualifiers = ["is", "was"]  # "the year is 2021"

    more_markers = ["plus", "add", "+"]
    less_markers = ["minus", "subtract", "-"]
    past_markers = ["past", "last"]
    future_markers = ["next"]
    most_recent_qualifiers = ["last"]

    now = ["now"]
    today = ["today"]
    this = ["this", "current", "present"]
    tomorrow = ["tomorrow"]
    yesterday = ["yesterday"]
    day_literal = ["day", "days"]
    week_literal = ["week", "weeks"]
    weekend_literal = ["weekend", "weekends"]
    month_literal = ["month", "months"]
    year_literal = ["year", "years"]
    century_literal = ["century", "centuries"]
    decade_literal = ["decade", "decades"]
    millennium_literal = ["millennium", "millenia", "millenniums"]
    hemisphere_literal = ["hemisphere"]
    season_literal = ["season"]

    date_words = _tokenize_en(date_str)

    # check for word boundaries and parse reference dates
    index = 0
    is_relative = False
    is_relative_past = False
    is_past = False
    is_sum = False
    is_subtract = False
    is_of = False
    delta = None

    # is this a negative timespan?
    for marker in past_qualifiers:
        if marker in date_words:
            is_past = True
            index = date_words.index(marker)

    # is this relative to (after) a date?
    for marker in relative_qualifiers:
        if marker in date_words:
            is_relative = True
            index = date_words.index(marker)

    # is this relative to (before) a date?
    for marker in relative_past_qualifiers:
        if marker in date_words:
            is_relative_past = True
            index = date_words.index(marker)

    # is this a timespan in the future?
    for marker in more_markers:
        if marker in date_words:
            is_sum = True
            index = date_words.index(marker)

    # is this a timespan in the past?
    for marker in less_markers:
        if marker in date_words:
            is_subtract = True
            index = date_words.index(marker)

    # cardinal of thing
    # 3rd day of the 4th month of 1994
    for marker in of_qualifiers:
        if marker in date_words:
            is_of = True
            index = date_words.index(marker)

    # is there some geographical information?
    for idx, word in enumerate(date_words):
        # this is used to parse seasons, which depend on geographical location
        # "i know what you did last summer",  "winter is coming"
        # usually this will be set automatically based on user location
        # this adds a naive check for "summer in north hemisphere"
        # TODO extracting location string (NER)?
        wordNext = date_words[idx + 1] if idx + 1 < len(date_words) else ""
        word = word.rstrip('s')
        if word in HEMISPHERES_EN[Hemisphere.NORTH] and \
                wordNext in hemisphere_literal:
            hemisphere = Hemisphere.NORTH
        elif word in HEMISPHERES_EN[Hemisphere.SOUTH] and \
                wordNext in hemisphere_literal:
            hemisphere = Hemisphere.SOUTH

    # parse Nth {X} of Nth {Y}
    if is_of:
        # parse {ORDINAL} day/week/month/year... of {date}
        _ordinal_words = date_words[:index]  # 3rd day / 4th week of the year
        _number = None

        _unit = "day"  # TODO is this a sane default ?
        _res = DateResolution.DAY_OF_MONTH

        # parse "{NUMBER} {day/week/month/year...} "
        if len(_ordinal_words) > 1:
            _ordinal = _ordinal_words[-2]
            _unit = _ordinal_words[-1]
            if is_numeric(_ordinal):
                _number = int(_ordinal)
            # parse "last {day/week/month/year...} "
            elif _ordinal_words[0] in most_recent_qualifiers:
                _number = -1

        # parse "{NUMBER}"
        elif len(_ordinal_words) == 1:
            _ordinal = _ordinal_words[0]
            if is_numeric(_ordinal):
                _number = int(_ordinal)

        # parse resolution
        if _number:
            _date_words = date_words[index + 1:]
            _best_idx = len(_date_words) - 1

            # parse "Nth {day/week/month/year...} of {YEAR}"
            if len(_date_words) and is_numeric(_date_words[0]) \
                    and len(_date_words[0]) == 4:
                ref_date = date(day=1, month=1, year=int(_date_words[0]))
                _res = DateResolution.DAY_OF_YEAR

            # parse "{NUMBER} day
            if _unit in day_literal:
                # parse "{NUMBER} day of month
                for marker in month_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.DAY_OF_MONTH
                # parse "{NUMBER} day of year
                for marker in year_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.DAY_OF_YEAR
                # parse "{NUMBER} day of decade
                for marker in decade_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.DAY_OF_DECADE
                # parse "{NUMBER} day of century
                for marker in century_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.DAY_OF_CENTURY
                # parse "{NUMBER} day of millennium
                for marker in millennium_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.DAY_OF_MILLENIUM

            # parse "{NUMBER} week
            if _unit in week_literal:
                _res = DateResolution.WEEK_OF_MONTH
                # parse "{NUMBER} week of Nth month
                for marker in month_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.WEEK_OF_MONTH
                # parse "{NUMBER} week of Nth year
                for marker in year_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.WEEK_OF_YEAR
                # parse "{NUMBER} week of Nth decade
                for marker in decade_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.WEEK_OF_DECADE
                # parse "{NUMBER} week of Nth century
                for marker in century_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.WEEK_OF_CENTURY
                # parse "{NUMBER} week of Nth millennium
                for marker in millennium_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.WEEK_OF_MILLENIUM

            # parse "{NUMBER} month
            if _unit in month_literal:
                # parse "{NUMBER} month of Nth year
                _res = DateResolution.MONTH_OF_YEAR
                for marker in year_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.MONTH_OF_YEAR
                # parse "{NUMBER} month of Nth decade
                for marker in decade_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.MONTH_OF_DECADE
                # parse "{NUMBER} month of Nth century
                for marker in century_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        _res = DateResolution.MONTH_OF_CENTURY
                # parse "{NUMBER} month of Nth millenium
                for marker in millennium_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.MONTH_OF_MILLENIUM

            # parse "{NUMBER} year
            if _unit in year_literal:
                _res = DateResolution.YEAR
                for marker in year_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.YEAR
                for marker in decade_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.YEAR_OF_DECADE
                for marker in century_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.YEAR_OF_CENTURY
                for marker in millennium_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.YEAR_OF_MILLENIUM

            # parse "{NUMBER} decade
            if _unit in decade_literal:
                _res = DateResolution.DECADE
                for marker in century_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.DECADE_OF_CENTURY
                for marker in millennium_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.DECADE_OF_MILLENIUM

            # parse "{NUMBER} century
            if _unit in century_literal:
                _res = DateResolution.CENTURY
                for marker in millennium_literal:
                    if marker in _date_words:
                        _idx = _date_words.index(marker)
                        if _idx <= _best_idx:
                            _best_idx = _idx
                            _res = DateResolution.CENTURY_OF_MILLENIUM

            # parse "{NUMBER} millenniu
            if _unit in millennium_literal:
                _res = DateResolution.MILLENNIUM

            _date_str = " ".join(_date_words)
            _extracted_date = extract_date_en(_date_str, ref_date,
                                              resolution, hemisphere)
            if not _extracted_date:
                _year = _date_words[0]
                if is_numeric(_year) and len(_year) == 4:
                    _extracted_date = get_ordinal(_year,
                                                  resolution=DateResolution.YEAR)
            return get_ordinal(_number, _extracted_date, _res)

    # parse {duration} ago
    if is_past:
        # parse {duration} ago
        duration_str = " ".join(date_words[:index])
        delta, remainder = extract_duration_en(duration_str)
        if not delta:
            raise RuntimeError(
                "Could not extract duration from: " + duration_str)

    # parse {duration} after {date}
    if is_relative:
        # parse {duration} from {reference_date}
        # 1 hour 3 minutes from now
        # 5 days from now
        # 3 weeks after tomorrow
        # 5 days before today/tomorrow/tuesday

        duration_str = " ".join(date_words[:index])
        if duration_str:
            delta, remainder = extract_duration_en(duration_str)

            _date_str = " ".join(date_words[index + 1:])
            _extracted_date = extract_date_en(_date_str, ref_date)
            if not _extracted_date and len(date_words) > index + 1:
                _year = date_words[index + 1]
                if len(_year) == 4 and is_numeric(_year):
                    _extracted_date = date(day=1, month=1, year=int(_year))
            return (_extracted_date or ref_date) + delta
        else:
            _date_str = " ".join(date_words[index + 1:])
            _extracted_date = extract_date_en(_date_str, ref_date)
            if not _extracted_date:
                _year = date_words[index + 1]
                if len(_year) == 4 and is_numeric(_year):
                    _extracted_date = date(day=1, month=1, year=int(_year))

            ref_date = _extracted_date or ref_date

            # next day
            if resolution == DateResolution.DAY:
                return ref_date + timedelta(days=1)
            # next week
            elif resolution == DateResolution.WEEK:
                delta = timedelta(weeks=1)
                _extracted_date = ref_date + delta
                _start, _end = get_week_range(_extracted_date)
                return _start
            # next month
            elif resolution == DateResolution.MONTH:
                delta = timedelta(days=31)
                _extracted_date = ref_date + delta
                _start, _end = get_month_range(_extracted_date)
                return _start
            # next year
            elif resolution == DateResolution.YEAR:
                delta = timedelta(days=31 * 12)
                _extracted_date = ref_date + delta
                _start, _end = get_year_range(_extracted_date)
                return _start
            # next decade
            elif resolution == DateResolution.DECADE:
                delta = timedelta(days=366 * 10)
                _extracted_date = ref_date + delta
                _start, _end = get_decade_range(_extracted_date)
                return _start
            # next century
            elif resolution == DateResolution.CENTURY:
                delta = timedelta(days=366 * 100)
                _extracted_date = ref_date + delta
                _start, _end = get_century_range(_extracted_date)
                return _start
            # next millennium
            elif resolution == DateResolution.MILLENNIUM:
                delta = timedelta(days=366 * 1000)
                _extracted_date = ref_date + delta
                _start, _end = get_millennium_range(_extracted_date)
                return _start
            else:
                raise ValueError("Invalid Resolution")

    # parse {duration} before {date}
    if is_relative_past:
        # parse {duration} from {reference_date}
        # 1 hour 3 minutes from now
        # 5 days from now
        # 3 weeks after tomorrow
        # 5 days before today/tomorrow/tuesday

        duration_str = " ".join(date_words[:index])
        if duration_str:
            delta, remainder = extract_duration_en(duration_str)
            _date_str = " ".join(date_words[index + 1:])
            _extracted_date = extract_date_en(_date_str, ref_date)
            if not _extracted_date and len(date_words) > index + 1:
                _year = date_words[index + 1]
                if len(_year) == 4 and is_numeric(_year):
                    _extracted_date = date(day=1, month=1, year=int(_year))
            return (_extracted_date or ref_date) - delta
        else:
            _date_str = " ".join(date_words[index + 1:])
            _extracted_date = extract_date_en(_date_str, ref_date)
            if not _extracted_date:
                _year = date_words[index + 1]
                if len(_year) == 4 and is_numeric(_year):
                    _extracted_date = date(day=1, month=1, year=int(_year))

            ref_date = _extracted_date or ref_date
            # previous day
            if resolution == DateResolution.DAY:
                return ref_date - timedelta(days=1)
            # previous week
            elif resolution == DateResolution.WEEK:
                _extracted_date = ref_date - timedelta(weeks=1)
                _start, _end = get_week_range(_extracted_date)
                return _start
            # previous month
            elif resolution == DateResolution.MONTH:
                delta = timedelta(days=30)
                _extracted_date = ref_date - delta
                _start, _end = get_month_range(_extracted_date)
                return _start
            # previous year
            elif resolution == DateResolution.YEAR:
                delta = timedelta(days=365)
                _extracted_date = ref_date - delta
                _start, _end = get_year_range(_extracted_date)
                return _start
            # previous decade
            elif resolution == DateResolution.DECADE:
                delta = timedelta(days=365 * 10)
                _extracted_date = ref_date - delta
                _start, _end = get_decade_range(ref_date)
                return _start
            # previous century
            elif resolution == DateResolution.CENTURY:
                delta = timedelta(days=365 * 100)
                _extracted_date = ref_date - delta
                _start, _end = get_century_range(ref_date)
                return _start
            # previous millennium
            elif resolution == DateResolution.MILLENNIUM:
                delta = timedelta(days=365 * 1000)
                _extracted_date = ref_date - delta
                _start, _end = get_century_range(ref_date)
                return _start
            else:
                raise ValueError("Invalid Sensitivity")

    # parse {date} plus/minus {duration}
    if is_sum or is_subtract:
        # parse {reference_date} plus {duration}
        # january 5 plus 2 weeks
        # parse {reference_date} minus {duration}
        # now minus 10 days
        duration_str = " ".join(date_words[index + 1:])
        delta, remainder = extract_duration_en(duration_str)

        if not delta:
            raise RuntimeError(
                "Could not extract duration from: " + duration_str)
        _date_str = " ".join(date_words[:index])
        _extracted_date = extract_date_en(_date_str, ref_date)
        if not _extracted_date and len(date_words) > index + 1:
            _year = date_words[index + 1]
            if len(_year) == 4 and is_numeric(_year):
                _extracted_date = date(day=1, month=1, year=int(_year))
        ref_date = _extracted_date or ref_date

    # relative timedelta found
    if delta:
        try:
            if is_past or is_subtract:
                extracted_date = ref_date - delta
            else:
                extracted_date = ref_date + delta
            if isinstance(extracted_date, datetime):
                extracted_date = extracted_date.date()
            return extracted_date
        except OverflowError:
            # TODO how to handle BC dates
            # https://stackoverflow.com/questions/15857797/bc-dates-in-python
            year_bc = delta.days // 365 - ref_date.year
            bc_str = str(year_bc) + " BC"
            print("ERROR: extracted date is " + bc_str)
            raise

    # iterate the word list to extract a date
    else:
        date_found = False
        extracted_date = ref_date
        extracted_date = extracted_date
        current_date = now_local()
        final_date = False
        for idx, word in enumerate(date_words):
            if final_date:
                break  # no more date updates allowed

            if word == "":
                continue

            wordPrevPrev = date_words[idx - 2] if idx > 1 else ""
            wordPrev = date_words[idx - 1] if idx > 0 else ""
            wordNext = date_words[idx + 1] if idx + 1 < len(date_words) else ""
            wordNextNext = date_words[idx + 2] if idx + 2 < len(
                date_words) else ""
            wordNextNextNext = date_words[idx + 3] if idx + 3 < len(
                date_words) else ""

            # TODO NER for locations in date_str and parse hemisphere
            if word in HEMISPHERES_EN[Hemisphere.NORTH] and \
                    wordNext in hemisphere_literal:
                hemisphere = Hemisphere.NORTH
            elif word in HEMISPHERES_EN[Hemisphere.SOUTH] and \
                    wordNext in hemisphere_literal:
                hemisphere = Hemisphere.SOUTH

            # parse "now"
            if word in now:
                date_found = True
                extracted_date = current_date
            # parse "today"
            if word in today:
                date_found = True
                extracted_date = ref_date
            # parse "yesterday"
            if word in yesterday:
                date_found = True
                extracted_date = ref_date - timedelta(days=1)
            # parse "tomorrow"
            if word in tomorrow:
                date_found = True
                extracted_date = ref_date + timedelta(days=1)
            # parse {weekday}
            if weekday_to_int(word, "en"):
                date_found = True
                int_week = weekday_to_int(word, "en")
                _w = extracted_date.weekday()
                _delta = 0
                if wordPrev in past_markers:
                    # parse last {weekday}
                    if int_week == _w:
                        _delta = 7
                    elif int_week < _w:
                        _delta = _w - int_week
                    else:
                        _delta = 7 - int_week + _w
                    extracted_date -= timedelta(days=_delta)
                else:
                    # parse this {weekday}
                    # parse next {weekday}
                    if int_week < _w:
                        _delta = 7 - _w + int_week
                    else:
                        _delta = int_week - _w
                    extracted_date += timedelta(days=_delta)
                assert extracted_date.weekday() == int_week
            # parse {month}
            if month_to_int(word, "en"):
                date_found = True
                int_month = month_to_int(word, "en")

                extracted_date = ref_date.replace(month=int_month, day=1)

                if wordPrev in past_markers:
                    if int_month > ref_date.month:
                        extracted_date = extracted_date.replace(
                            year=ref_date.year - 1)
                elif wordPrev in future_markers:
                    if int_month < ref_date.month:
                        extracted_date = extracted_date.replace(
                            year=ref_date.year + 1)

                if is_numeric(wordNext) and 0 < int(wordNext) <= 31:
                    # parse {month} {DAY_OF_MONTH}
                    extracted_date = extracted_date.replace(day=int(wordNext))
                    # parse {month} {DAY_OF_MONTH} {YYYY}
                    if len(wordNextNext) == 4 and is_numeric(wordNextNext):
                        extracted_date = extracted_date \
                            .replace(year=int(wordNextNext))

                elif is_numeric(wordPrev):
                    # parse {DAY_OF_MONTH} {month}
                    extracted_date = extracted_date.replace(day=int(wordPrev))

                if is_numeric(wordNext) and len(wordNext) == 4:
                    # parse {month} {YEAR}
                    extracted_date = extracted_date.replace(year=int(wordNext))
                elif is_numeric(wordPrev) and len(wordPrev) == 4:
                    # parse {YEAR} {month}
                    extracted_date = extracted_date.replace(year=int(wordPrev))
            # parse "season"
            if word in season_literal:
                _start, _end = get_season_range(ref_date,
                                                hemisphere=hemisphere)
                # parse "in {Number} seasons"
                if is_numeric(wordPrev):
                    date_found = True
                    raise NotImplementedError
                # parse "this season"
                elif wordPrev in this:
                    date_found = True
                    extracted_date = _start
                # parse "last season"
                elif wordPrev in past_markers:
                    date_found = True
                    _end = _start - timedelta(days=2)
                    s = date_to_season(_end, hemisphere)
                    extracted_date = last_season_date(s, ref_date, hemisphere)
                # parse "next season"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = _end + timedelta(days=1)
            # parse "spring"
            if word in SEASONS_EN[Season.SPRING]:
                # parse "in {Number} springs"
                if is_numeric(wordPrev):
                    date_found = True
                    raise NotImplementedError
                # parse "this spring"
                elif wordPrev in this:
                    date_found = True
                    extracted_date = season_to_date(Season.SPRING,
                                                    ref_date,
                                                    hemisphere)
                # parse "last spring"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = last_season_date(Season.SPRING,
                                                      ref_date,
                                                      hemisphere)
                # parse "next spring"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = next_season_date(Season.SPRING,
                                                      ref_date,
                                                      hemisphere)
            # parse "fall"
            if word in SEASONS_EN[Season.FALL]:
                # parse "in {Number} falls"
                if is_numeric(wordPrev):
                    date_found = True
                    raise NotImplementedError
                # parse "this fall"
                elif wordPrev in this:
                    date_found = True
                    extracted_date = season_to_date(Season.FALL,
                                                    ref_date,
                                                    hemisphere)
                # parse "last fall"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = last_season_date(Season.FALL, ref_date,
                                                      hemisphere)
                # parse "next fall"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = next_season_date(Season.FALL, ref_date,
                                                      hemisphere)
            # parse "summer"
            if word in SEASONS_EN[Season.SUMMER]:
                # parse "in {Number} summers"
                if is_numeric(wordPrev):
                    date_found = True
                    raise NotImplementedError
                # parse "this summer"
                elif wordPrev in this:
                    date_found = True
                    extracted_date = season_to_date(Season.SUMMER,
                                                    ref_date,
                                                    hemisphere)
                # parse "last summer"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = last_season_date(Season.SUMMER, ref_date,
                                                      hemisphere)
                # parse "next summer"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = next_season_date(Season.SUMMER, ref_date,
                                                      hemisphere)
            # parse "winter"
            if word in SEASONS_EN[Season.WINTER]:
                # parse "in {Number} winters"
                if is_numeric(wordPrev):
                    date_found = True
                    raise NotImplementedError
                # parse "this winter"
                elif wordPrev in this:
                    date_found = True
                    extracted_date = season_to_date(Season.WINTER,
                                                    ref_date,
                                                    hemisphere)
                # parse "last winter"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = last_season_date(Season.WINTER, ref_date,
                                                      hemisphere)
                # parse "next winter"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = next_season_date(Season.WINTER, ref_date,
                                                      hemisphere)
            # parse "day"
            if word in day_literal:
                # parse {ORDINAL} day
                if is_numeric(wordPrev):
                    date_found = True
                    extracted_date = extracted_date.replace(day=int(wordPrev))
                # parse day {NUMBER}
                elif is_numeric(wordNext):
                    date_found = True
                    extracted_date = extracted_date.replace(day=int(wordNext))
                # parse "present day"
                elif wordPrev in this:
                    date_found = True
                    extracted_date = ref_date
            # parse "weekend"
            if word in weekend_literal:
                _is_weekend = ref_date.weekday() >= 5
                # parse {ORDINAL} weekend
                if is_numeric(wordPrev):
                    date_found = True
                    raise NotImplementedError
                # parse weekend {NUMBER}
                elif is_numeric(wordNext):
                    date_found = True
                    raise NotImplementedError
                # parse "this weekend"
                elif wordPrev in this:
                    date_found = True
                    _start, _end = get_weekend_range(ref_date)
                    extracted_date = _start
                # parse "next weekend"
                elif wordPrev in future_markers:
                    date_found = True
                    if not _is_weekend:
                        _start, _end = get_weekend_range(ref_date)
                    else:
                        _start, _end = get_weekend_range(ref_date +
                                                         timedelta(weeks=1))
                    extracted_date = _start
                # parse "last weekend"
                elif wordPrev in past_markers:
                    date_found = True
                    _start, _end = get_weekend_range(ref_date -
                                                     timedelta(weeks=1))
                    extracted_date = _start
            # parse "week"
            if word in week_literal:
                # parse {ORDINAL} week
                if is_numeric(wordPrev) and 0 < int(wordPrev) <= 4 * 12:
                    date_found = True
                    extracted_date = get_ordinal(int(wordPrev), ref_date,
                                                 resolution=DateResolution.WEEK_OF_YEAR)
                # parse "this week"
                if wordPrev in this:
                    date_found = True
                    _start, _end = get_week_range(ref_date)
                    extracted_date = _start
                # parse "last week"
                elif wordPrev in past_markers:
                    date_found = True
                    _last_week = ref_date - timedelta(weeks=1)
                    _start, _end = get_week_range(_last_week)
                    extracted_date = _start
                # parse "next week"
                elif wordPrev in future_markers:
                    date_found = True
                    _last_week = ref_date + timedelta(weeks=1)
                    _start, _end = get_week_range(_last_week)
                    extracted_date = _start
                # parse week {NUMBER}
                elif is_numeric(wordNext) and 0 < int(wordNext) <= 12:
                    date_found = True
                    extracted_date = get_ordinal(int(wordNext), ref_date,
                                                 resolution=DateResolution.WEEK_OF_YEAR)
            # parse "month"
            if word in month_literal:

                # parse {ORDINAL} month
                if is_numeric(wordPrev) and 0 < int(wordPrev) <= 12:
                    date_found = True
                    extracted_date = get_ordinal(int(wordPrev), ref_date,
                                                 DateResolution.MONTH_OF_YEAR)
                # parse month {NUMBER}
                elif is_numeric(wordNext) and 0 < int(wordNext) <= 12:
                    date_found = True
                    extracted_date = get_ordinal(int(wordNext), ref_date,
                                                 DateResolution.MONTH_OF_YEAR)
                # parse "this month"
                elif wordPrev in this:
                    date_found = True
                    extracted_date = ref_date.replace(day=1)
                # parse "next month"
                elif wordPrev in future_markers:
                    date_found = True
                    _next_month = ref_date + timedelta(days=30)
                    extracted_date = _next_month.replace(day=1)
                # parse "last month"
                elif wordPrev in past_markers:
                    date_found = True
                    _last_month = ref_date - timedelta(days=30)
                    extracted_date = _last_month.replace(day=1)
            # parse "year"
            if word in year_literal:
                # parse "current year"
                if wordPrev in this:
                    date_found = True
                    extracted_date = get_ordinal(ref_date.year,
                                                 resolution=DateResolution.YEAR)
                # parse "last year"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = get_ordinal(ref_date.year - 1,
                                                 resolution=DateResolution.YEAR)
                # parse "next year"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = get_ordinal(ref_date.year + 1,
                                                 resolution=DateResolution.YEAR)
                # parse Nth year
                elif is_numeric(wordPrev):
                    date_found = True
                    extracted_date = get_ordinal(int(wordPrev) - 1,
                                                 resolution=DateResolution.YEAR)
            # parse "decade"
            if word in decade_literal:
                _decade = (ref_date.year // 10) + 1
                # parse "current decade"
                if wordPrev in this:
                    date_found = True
                    extracted_date = get_ordinal(_decade,
                                                 resolution=DateResolution.DECADE)
                # parse "last decade"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = get_ordinal(_decade - 1,
                                                 resolution=DateResolution.DECADE)
                # parse "next decade"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = get_ordinal(_decade + 1,
                                                 resolution=DateResolution.DECADE)
                # parse Nth decade
                elif is_numeric(wordPrev):
                    date_found = True
                    extracted_date = get_ordinal(int(wordPrev),
                                                 resolution=DateResolution.DECADE)
            # parse "millennium"
            if word in millennium_literal:
                _mil = ref_date.year // 1000
                # parse "current millennium"
                if wordPrev in this:
                    date_found = True
                    extracted_date = get_ordinal(_mil, ref_date,
                                                 DateResolution.MILLENNIUM)
                # parse "last millennium"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = get_ordinal(_mil - 1, ref_date,
                                                 DateResolution.MILLENNIUM)
                # parse "next millennium"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = get_ordinal(_mil + 1, ref_date,
                                                 DateResolution.MILLENNIUM)
                # parse Nth millennium
                elif is_numeric(wordPrev):
                    date_found = True

                    extracted_date = get_ordinal(int(wordPrev) - 1,
                                                 extracted_date,
                                                 DateResolution.MILLENNIUM)
            # parse "century"
            if word in century_literal:
                _century = ref_date.year // 100
                # parse "current century"
                if wordPrev in this:
                    date_found = True
                    extracted_date = get_ordinal(_century, ref_date,
                                                 DateResolution.CENTURY)
                # parse "last century"
                elif wordPrev in past_markers:
                    date_found = True
                    extracted_date = get_ordinal(_century - 1,
                                                 ref_date,
                                                 DateResolution.CENTURY)
                # parse "next century"
                elif wordPrev in future_markers:
                    date_found = True
                    extracted_date = get_ordinal(_century + 1,
                                                 ref_date,
                                                 DateResolution.CENTURY)
                # parse Nth century
                elif is_numeric(wordPrev):
                    date_found = True

                    extracted_date = get_ordinal(int(wordPrev) - 1,
                                                 extracted_date,
                                                 DateResolution.CENTURY)
            # parse day/mont/year is NUMBER
            if word in set_qualifiers and is_numeric(wordNext):
                _ordinal = int(wordNext)
                if wordPrev in day_literal:
                    date_found = True
                    extracted_date = get_ordinal(_ordinal, extracted_date,
                                                 DateResolution.DAY_OF_MONTH)
                elif wordPrev in month_literal:
                    date_found = True
                    extracted_date = get_ordinal(_ordinal, extracted_date,
                                                 DateResolution.MONTH_OF_YEAR)
                elif wordPrev in year_literal:
                    date_found = True
                    extracted_date = get_ordinal(_ordinal, extracted_date,
                                                 DateResolution.YEAR)
                elif wordPrev in decade_literal:
                    date_found = True
                    extracted_date = get_ordinal(_ordinal, extracted_date,
                                                 DateResolution.DECADE)
                elif wordPrev in century_literal:
                    date_found = True
                    extracted_date = get_ordinal(_ordinal, extracted_date,
                                                 DateResolution.CENTURY)
                elif wordPrev in millennium_literal:
                    date_found = True
                    extracted_date = get_ordinal(_ordinal, extracted_date,
                                                 DateResolution.MILLENNIUM)
                # TODO week of month vs week of year

    if date_found:
        if isinstance(extracted_date, datetime):
            extracted_date = extracted_date.date()
        return extracted_date
    return None


if __name__ == "__main__":
    ref_date = date(2117, 2, 3)
    now = now_local()
    default_time = now.time()


    def _test_date(date_str, expected_date,
                   resolution=DateResolution.DAY,
                   anchor=None, hemi=Hemisphere.NORTH):
        anchor = anchor or ref_date
        if isinstance(expected_date, datetime):
            expected_date = expected_date.date()
        extracted_date = extract_date_en(date_str, anchor, resolution,
                                         hemisphere=hemi)

        print("expected   | extracted  | input")
        print(expected_date, "|", extracted_date, "|", date_str, )
        assert extracted_date == expected_date


    def test_now():
        _test_date("now", now)
        _test_date("today", ref_date)
        _test_date("tomorrow", ref_date + timedelta(days=1))
        _test_date("yesterday", ref_date - timedelta(days=1))
        _test_date("twenty two thousand days before now",
                   now - timedelta(days=22000))
        _test_date("10 days from now",
                   now + timedelta(days=10))


    def test_duration_ago():
        _test_date("twenty two weeks ago",
                   ref_date - timedelta(weeks=22))
        _test_date("twenty two months ago",
                   ref_date - timedelta(days=30 * 22))
        _test_date("twenty two decades ago",
                   ref_date - timedelta(days=365 * 10 * 22))
        _test_date("1 century ago",
                   ref_date - timedelta(days=365 * 100))
        _test_date("ten centuries ago",
                   ref_date - timedelta(days=365 * 100 * 10))
        _test_date("two millenniums ago",
                   ref_date - timedelta(days=365 * 1000 * 2))
        _test_date("twenty two thousand days ago",
                   ref_date - timedelta(days=22000))
        try:
            _test_date("twenty two thousand years ago",
                       ref_date - timedelta(days=365 * 22000))
        except OverflowError as e:
            # ERROR: extracted date is 19980 BC
            assert str(e) == "date value out of range"


    def test_spoken_date():
        _test_date("13 may 1992", date(month=5, year=1992, day=13))
        _test_date("march 1st 2020", date(month=3, year=2020, day=1))
        _test_date("29 november", date(month=11,
                                       year=ref_date.year,
                                       day=29))
        _test_date("january 2020", date(month=1,
                                        year=2020,
                                        day=1))
        _test_date("day 1", date(month=ref_date.month,
                                 year=ref_date.year,
                                 day=1))
        _test_date("1 of september",
                   ref_date.replace(day=1, month=9, year=ref_date.year))
        _test_date("march 13th",
                   ref_date.replace(day=13, month=3, year=ref_date.year))
        _test_date("12 may",
                   ref_date.replace(day=12, month=5, year=ref_date.year))


    def test_from():
        _test_date("10 days from today",
                   ref_date + timedelta(days=10))
        _test_date("10 days from tomorrow",
                   ref_date + timedelta(days=11))
        _test_date("10 days from yesterday",
                   ref_date + timedelta(days=9))
        # _test_date("10 days from after tomorrow",  # TODO fix me
        #          ref_date + timedelta(days=12))


    def test_ordinals():
        _test_date("the 5th day", ref_date.replace(day=5))
        _test_date("the fifth day",
                   date(month=ref_date.month, year=ref_date.year, day=5))
        _test_date("the 20th day of 4th month",
                   ref_date.replace(month=4, day=20))
        _test_date("the 20th day of month 4",
                   ref_date.replace(month=4, day=20))
        _test_date("6th month of 1992", date(month=6, year=1992, day=1))
        _test_date("first day of the 10th month of 1969",
                   ref_date.replace(day=1, month=10, year=1969))
        _test_date("2nd day of 2020",
                   ref_date.replace(day=2, month=1, year=2020))
        _test_date("300 day of 2020",
                   ref_date.replace(day=1, month=1, year=2020) +
                   timedelta(days=299))


    def test_plus():
        _test_date("now plus 10 days",
                   now + timedelta(days=10))
        _test_date("today plus 10 days",
                   ref_date + timedelta(days=10))
        _test_date("yesterday plus 10 days",
                   ref_date + timedelta(days=9))
        _test_date("tomorrow plus 10 days",
                   ref_date + timedelta(days=11))
        # _test_date("tomorrow + 10 days",
        #           ref_date + timedelta(days=11))
        _test_date("today plus 10 months",
                   ref_date + timedelta(days=30 * 10))
        _test_date("today plus 10 years",
                   ref_date + timedelta(days=10 * 365))
        _test_date("today plus 10 years, 10 months and 1 day",
                   ref_date + timedelta(days=10 * 365 + 10 * 30 + 1))


    def test_minus():
        _test_date("now minus 10 days",
                   now - timedelta(days=10))
        _test_date("today minus 10 days",
                   ref_date - timedelta(days=10))
        # _test_date("today - 10 days",
        #           ref_date - timedelta(days=10))
        # _test_date("yesterday - 10 days",  # TODO fix me
        #           ref_date - timedelta(days=11))
        _test_date("tomorrow minus 10 days",
                   ref_date - timedelta(days=9))
        _test_date("today minus 10 months",
                   ref_date - timedelta(days=30 * 10))
        # _test_date("today - 10 years",  # TODO fix me
        #            ref_date.replace(year=ref_date.year - 10))
        _test_date("today minus 10 years, 10 months and 1 day",
                   ref_date - timedelta(days=10 * 365 + 10 * 30 + 1))


    def test_before():
        # before -> nearest DateResolution.XXX
        _test_date("before today",
                   ref_date - timedelta(days=1))
        _test_date("before tomorrow", ref_date)
        _test_date("before yesterday",
                   ref_date - timedelta(days=2))
        _test_date("before march 12",
                   ref_date.replace(month=3, day=11))

        _test_date("before 1992", date(year=1991, month=12, day=31))
        _test_date("before 1992", date(year=1991, day=1, month=1),
                   DateResolution.YEAR)
        _test_date("before 1992", date(year=1990, day=1, month=1),
                   DateResolution.DECADE)
        _test_date("before 1992", date(year=1900, day=1, month=1),
                   DateResolution.CENTURY)

        _test_date("before april",
                   date(month=3, day=31, year=ref_date.year))
        _test_date("before april",
                   date(month=1, day=1, year=ref_date.year - 1),
                   DateResolution.YEAR)
        _test_date("before april",
                   date(month=1, day=1, year=2110),
                   DateResolution.DECADE)

        _test_date("before april 1992",
                   date(month=3, day=31, year=1992))
        _test_date("before april 1992",
                   date(month=1, day=1, year=1991),
                   DateResolution.YEAR)
        _test_date("before april 1992",
                   date(month=1, day=1, year=1990),
                   DateResolution.DECADE)


    def test_after():
        # after -> next DateResolution.XXX
        _test_date("after today",
                   ref_date + timedelta(days=1))
        _test_date("after yesterday", ref_date)
        _test_date("after tomorrow",
                   ref_date + timedelta(days=2))

        _test_date("after today",
                   ref_date.replace(day=8),
                   DateResolution.WEEK)
        _test_date("after today",
                   date(day=1, month=ref_date.month + 1, year=ref_date.year),
                   DateResolution.MONTH)
        _test_date("after tomorrow",
                   date(day=1, month=1, year=2120),
                   DateResolution.DECADE)

        _test_date("after march 12",
                   ref_date.replace(month=3, day=12) + timedelta(days=1))

        _test_date("after 1992", date(year=1992, day=2, month=1))
        _test_date("after 1992", date(year=1992, day=6, month=1),
                   DateResolution.WEEK)
        _test_date("after 1992", date(year=1992, day=1, month=2),
                   DateResolution.MONTH)
        _test_date("after 1992", date(year=1993, day=1, month=1),
                   DateResolution.YEAR)
        _test_date("after 1992", date(year=2000, day=1, month=1),
                   DateResolution.DECADE)
        _test_date("after 1992", date(year=2000, day=1, month=1),
                   DateResolution.CENTURY)
        _test_date("after 1992", date(year=2000, day=1, month=1),
                   DateResolution.MILLENNIUM)

        _test_date("after april",
                   date(day=2, month=4, year=ref_date.year))
        _test_date("after april",
                   date(day=1, month=4, year=ref_date.year) +
                   timedelta(days=1))
        _test_date("after april", date(year=ref_date.year, day=5, month=4),
                   DateResolution.WEEK)
        _test_date("after april", date(year=ref_date.year, day=1, month=5),
                   DateResolution.MONTH)
        _test_date("after april", date(year=2120, day=1, month=1),
                   DateResolution.DECADE)

        _test_date("after april 1992", date(year=1992, day=1, month=5),
                   DateResolution.MONTH)
        _test_date("after april 1992", date(year=1993, day=1, month=1),
                   DateResolution.YEAR)
        _test_date("after april 1992", date(year=2000, day=1, month=1),
                   DateResolution.CENTURY)

        _test_date("after 2600", date(year=2600, day=2, month=1))
        _test_date("after 2600", date(year=2600, day=1, month=2),
                   DateResolution.MONTH)
        _test_date("after 2600", date(year=2601, day=1, month=1),
                   DateResolution.YEAR)

        _test_date("after 2600", date(year=2610, day=1, month=1),
                   DateResolution.DECADE)
        _test_date("after 2600", date(year=2700, day=1, month=1),
                   DateResolution.CENTURY)


    def test_this():
        _current_century = ((ref_date.year // 100) - 1) * 100
        _current_decade = (ref_date.year // 10) * 10

        _test_date("this month", ref_date.replace(day=1))
        _test_date("this week", ref_date - timedelta(days=ref_date.weekday()))
        _test_date("this year", ref_date.replace(day=1, month=1))
        _test_date("current year", ref_date.replace(day=1, month=1))
        _test_date("present day", ref_date)
        _test_date("current decade", date(day=1, month=1, year=2110))
        _test_date("current century", date(day=1, month=1, year=2100))


    def test_next():
        _test_date("next month",
                   (ref_date + timedelta(days=30)).replace(day=1))
        _test_date("next week",
                   get_week_range(ref_date + timedelta(weeks=1))[0])
        _test_date("next century",
                   date(year=2200, day=1, month=1))
        _test_date("next year",
                   date(year=ref_date.year + 1, day=1, month=1))


    def test_last():
        _test_date("last month",
                   (ref_date - timedelta(days=30)).replace(day=1))
        _test_date("last week",
                   get_week_range(ref_date - timedelta(weeks=1))[0])
        _test_date("last year", date(year=ref_date.year - 1,
                                     day=1,
                                     month=1))
        _test_date("last century", date(year=2000, day=1, month=1))

        _test_date("last day of the 10th century",
                   date(day=31, month=12, year=999))

        _test_date("last day of this month",
                   ref_date.replace(day=28))
        # _test_date("last day of the month",
        #           ref_date.replace(day=28))

        _test_date("last day of this year",
                   date(day=31, month=12, year=ref_date.year))
        # _test_date("last day of the year",
        #            date(day=31, month=12, year=ref_date.year))

        _test_date("last day of this century",
                   date(day=31, month=12, year=2199))
        # _test_date("last day of the century",
        #           date(day=31, month=12, year=2199))

        _test_date("last day of this decade",
                   date(day=31, month=12, year=2119))
        _test_date("last day of the decade",
                   date(day=31, month=12, year=2119))
        _test_date("last day of this millennium",
                   date(day=31, month=12, year=2999))
        _test_date("last day of the millennium",
                   date(day=31, month=12, year=2999))
        _test_date("last day of the 20th month of the 5th millennium",
                   date(day=31, month=7, year=4001))
        _test_date("last day of the 9th decade of the 5th millennium",
                   date(day=31, month=12, year=4089))

        _test_date("last day of the 10th millennium",
                   date(day=31, month=12, year=9999))


    def test_first():
        _test_date("first day", ref_date.replace(day=1))
        _test_date("first day of this month", ref_date.replace(day=1))
        _test_date("first day of this year", ref_date.replace(day=1, month=1))
        _test_date("first day of this decade", date(day=1, month=1,
                                                    year=2110))
        _test_date("first day of this century", date(day=1, month=1,
                                                     year=2100))
        _test_date("first day of this millennium", date(day=1, month=1,
                                                        year=2000))

        _test_date("first month", ref_date.replace(day=1, month=1))

        # _test_date("first week", get_week_range(ref_date.replace(day=1))[0])
        _test_date("first decade", date(year=1, day=1, month=1))
        _test_date("first year", date(year=1, day=1, month=1))
        _test_date("first century", date(year=1, day=1, month=1))

        _test_date("first day of the 10th century",
                   date(day=1, month=1, year=900))

        # _test_date("first day of the month", ref_date.replace(day=1))
        # _test_date("first day of the year",
        #            date(day=1, month=1, year=ref_date.year))

        # _test_date("first day of the century",
        #           date(day=1, month=1, year=2100))
        _test_date("first day of the decade",
                   date(day=1, month=1, year=2110))
        _test_date("first day of the millennium",
                   date(day=1, month=1, year=2000))

        _test_date("first day of the 10th millennium",
                   date(day=1, month=1, year=9000))


    def test_seasons():
        # TODO last summer , next spring

        def _test_season_north(test_date, expected_date, season):
            _test_date(test_date, expected_date, hemi=Hemisphere.NORTH)
            assert date_to_season(expected_date,
                                  hemisphere=Hemisphere.NORTH) == season

        def _test_season_south(test_date, expected_date, season):
            _test_date(test_date, expected_date, hemi=Hemisphere.SOUTH)
            assert date_to_season(expected_date,
                                  hemisphere=Hemisphere.SOUTH) == season

        _test_season_north("this spring", ref_date.replace(day=1, month=3),
                           Season.SPRING)
        _test_season_south("this spring", ref_date.replace(day=1, month=9),
                           Season.SPRING)

        _test_season_north("next spring",  ref_date.replace(day=1, month=3),
                     Season.SPRING)
        _test_season_south("next spring", ref_date.replace(day=1, month=9),
                           Season.SPRING)

        _test_season_north("last spring",
                           date(day=1, month=3, year=ref_date.year - 1),
                     Season.SPRING)
        _test_season_south("last spring",
                           date(day=1, month=9, year=ref_date.year - 1),
                           Season.SPRING)

        _test_season_north("this summer", ref_date.replace(day=1, month=6),
                     Season.SUMMER)
        _test_season_north("next summer", ref_date.replace(day=1, month=6),
                     Season.SUMMER)
        _test_season_north("last summer", date(day=1, month=6,
                                       year=ref_date.year - 1),
                     Season.SUMMER)

        _test_season_north("this fall", ref_date.replace(day=1, month=9),
                     Season.FALL)
        _test_season_north("next fall", ref_date.replace(day=1, month=9),
                     Season.FALL)
        _test_season_north("last autumn",
                     date(day=1, month=9, year=ref_date.year - 1),
                     Season.FALL)

        _test_season_north("this winter", ref_date.replace(day=1, month=12),
                     Season.WINTER)
        _test_season_north("next winter", ref_date.replace(day=1, month=12),
                     Season.WINTER)
        _test_season_north("last winter",
                     ref_date.replace(day=1, month=12,
                                      year=ref_date.year - 1),
                     Season.WINTER)

        _ref_season = date_to_season(ref_date)
        print("reference season:", _ref_season)
        assert _ref_season == Season.WINTER
        _test_season_north("this season",
                     date(day=1, month=12,  year=ref_date.year - 1),
                     _ref_season)
        _test_season_north("next season",
                     date(day=1, month=3, year=ref_date.year),
                     Season.SPRING)

        _test_season_north("last season",
                     date(day=1, month=9, year=ref_date.year - 1),
                     Season.FALL)


    def test_weekends():
        # TODO plus / minus / after N weekends
        # TODO N weekends ago
        saturday, sunday = get_weekend_range(ref_date)
        assert saturday.weekday() == 5
        assert sunday.weekday() == 6

        _test_date("this weekend", saturday)
        _test_date("next weekend", saturday)
        _test_date("last weekend", saturday - timedelta(days=7))

        _test_date("this weekend", saturday,
                   anchor=saturday)
        _test_date("this weekend", saturday,
                   anchor=sunday)
        _test_date("next weekend", saturday + timedelta(days=7),
                   anchor=saturday)
        _test_date("next weekend", saturday + timedelta(days=7),
                   anchor=sunday)
        _test_date("last weekend", saturday - timedelta(days=7),
                   anchor=saturday)
        _test_date("last weekend", saturday - timedelta(days=7),
                   anchor=sunday)


    def test_is():
        _test_date("the year is 2100", date(year=2100, month=1, day=1))
        _test_date("the year was 1969", date(year=1969, month=1, day=1))
        _test_date("the day is 2", ref_date.replace(day=2))
        _test_date("the month is 8", ref_date.replace(month=8, day=1))

        _test_date("this is the second day of the third "
                   "month of the first year of the 9th millennium,",
                   date(day=2, month=3, year=8001))
        _test_date("this is the second day of the third "
                   "month of the 9th millennium,",
                   date(day=2, month=3, year=8000))
        # _test_date("this is the 9th millennium, the second day of the third "
        #           "month of the first year",
        #           date(day=2, month=3, year=8000))


    def test_of():
        _test_date("first day of the first millennium",
                   date(day=1, month=1, year=1))
        _test_date("first day of the first century",
                   date(day=1, month=1, year=1))
        _test_date("first day of the first decade",
                   date(day=1, month=1, year=1))
        _test_date("first day of the first year",
                   date(day=1, month=1, year=1))
        _test_date("first day of the first week",
                   date(day=1, month=1, year=ref_date.year))
        _test_date("3rd day",
                   ref_date.replace(day=3))
        _test_date("3rd day of may",
                   ref_date.replace(day=3, month=5))
        _test_date("3rd day of the 5th century",
                   date(day=3, month=1, year=400))
        _test_date("3rd day of the 5th month of the 10 century",
                   date(day=3, month=5, year=900))
        _test_date("25th month of the 10 century",
                   date(day=1, month=12, year=901))
        _test_date("3rd day of the 25th month of the 10 century",
                   date(day=3, month=12, year=901))
        _test_date("3rd day of 1973",
                   date(day=3, month=1, year=1973))
        _test_date("3rd day of the 17th decade",
                   date(day=3, month=1, year=160))
        _test_date("3rd day of the 10th millennium",
                   date(day=3, month=1, year=9000))
        _test_date("301st day of the 10th century",
                   date(day=28, month=10, year=900))
        _test_date("first century of the 6th millennium",
                   date(day=1, month=1, year=5000))
        _test_date("first decade of the 6th millennium",
                   date(day=1, month=1, year=5000))
        _test_date("39th decade of the 6th millennium",
                   date(day=1, month=1, year=5380))
        _test_date("the 20th year of the 6th millennium",
                   date(day=1, month=1, year=5020))
        _test_date("the 20th day of the 6th millennium",
                   date(day=20, month=1, year=5000))
        _test_date("last day of the 39th decade of the 6th millennium",
                   date(day=31, month=12, year=5389))


    def test_months():
        print("Reference month: ", int_to_month(ref_date.month))
        assert ref_date.month == 2
        _test_date("january", ref_date.replace(day=1, month=1))
        _test_date("last january", ref_date.replace(day=1, month=1))
        _test_date("next january", date(day=1, month=1,
                                        year=ref_date.year + 1))

        _test_date("in 29 november", date(day=29, month=11,
                                          year=ref_date.year))
        _test_date("last november 27", date(day=27, month=11,
                                            year=ref_date.year - 1))
        _test_date("next 3 november", date(day=3, month=11,
                                           year=ref_date.year))
        _test_date("last 3 november 1872", date(day=3, month=11, year=1872))


    def test_week():
        print("reference week day:", ref_date.weekday(), "date:", ref_date)
        _test_date("this week", ref_date.replace(day=1))
        _test_date("next week", ref_date.replace(day=8))
        _test_date("last week", ref_date.replace(day=25, month=1))

        _test_date("first week of this month",
                   ref_date.replace(day=1))
        _test_date("first week of this year",
                   ref_date.replace(day=1, month=1))
        _test_date("first week of this decade",
                   date(day=1, month=1, year=2110))
        _test_date("first week of this century",
                   date(day=1, month=1, year=2100))
        _test_date("first week of this millennium",
                   date(day=1, month=1, year=2000))

        _test_date("second week of this month",
                   ref_date.replace(day=8, month=2))
        _test_date("2nd week of this year",
                   ref_date.replace(day=8, month=1))
        _test_date("2nd week of this decade",
                   date(day=8, month=1, year=2110))
        _test_date("2 week of this century",
                   date(day=8, month=1, year=2100))
        _test_date("2 week of this millennium",
                   date(day=8, month=1, year=2000))

        _test_date("3rd week of this month",
                   ref_date.replace(day=15, month=2))
        _test_date("3rd week of this year",
                   ref_date.replace(day=15, month=1))
        _test_date("third week of this decade",
                   date(day=15, month=1, year=2110))
        _test_date("3 week of this century",
                   date(day=15, month=1, year=2100))
        _test_date("3 week of this millennium",
                   date(day=15, month=1, year=2000))

        _test_date("10th week of this year",
                   ref_date.replace(day=5, month=3))
        _test_date("100 week of this decade",
                   date(day=25, month=11, year=2111))
        _test_date("1000 week of this century",
                   date(day=24, month=2, year=2119))
        _test_date("10000 week of this millennium",
                   date(day=20, month=8, year=2191))

        _test_date("last week of this month",
                   ref_date.replace(day=22))
        _test_date("last week of this year",
                   ref_date.replace(day=27, month=12))
        _test_date("last week of this decade",
                   date(day=25, month=12, year=2119))
        _test_date("last week of this century",
                   date(day=30, month=12, year=2199))
        _test_date("last week of this millennium",
                   date(day=30, month=12, year=2999))


    test_week()
    test_now()
    test_before()
    test_after()
    test_duration_ago()
    test_spoken_date()
    test_from()
    test_plus()
    test_minus()
    test_ordinals()
    test_seasons()
    test_this()
    test_next()
    test_first()
    test_last()
    test_is()
    test_of()
    test_weekends()
    test_months()
