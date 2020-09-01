from enum import Enum
from lingua_franca.time import now_local
from datetime import date, timedelta


class Hemisphere(Enum):
    NORTH = 0
    SOUTH = 1


HEMISPHERES_EN = {
    Hemisphere.NORTH: ["north", "northern"],
    Hemisphere.SOUTH: ["south", "southern"]
}


class Season(Enum):
    SPRING = 0
    SUMMER = 1
    FALL = 2
    WINTER = 3


SEASONS_EN = {
    Season.SPRING: ["spring"],
    Season.WINTER: ["winter"],
    Season.SUMMER: ["summer"],
    Season.FALL: ["fall", "autumn"]
}


def date_to_season(ref_date=None, hemisphere=Hemisphere.NORTH):
    ref_date = ref_date or now_local().date()

    if hemisphere == Hemisphere.NORTH:
        fall = (
            date(day=1, month=9, year=ref_date.year),
            date(day=30, month=11, year=ref_date.year)
        )
        spring = (
            date(day=1, month=3, year=ref_date.year),
            date(day=31, month=5, year=ref_date.year)
        )
        summer = (
            date(day=1, month=6, year=ref_date.year),
            date(day=31, month=8, year=ref_date.year)
        )

        if fall[0] <= ref_date < fall[1]:
            return Season.FALL
        if summer[0] <= ref_date < summer[1]:
            return Season.SUMMER
        if spring[0] <= ref_date < spring[1]:
            return Season.SPRING
        return Season.WINTER

    else:
        spring = (
            date(day=1, month=9, year=ref_date.year),
            date(day=30, month=11, year=ref_date.year)
        )
        fall = (
            date(day=1, month=3, year=ref_date.year),
            date(day=31, month=5, year=ref_date.year)
        )
        winter = (
            date(day=1, month=6, year=ref_date.year),
            date(day=31, month=8, year=ref_date.year)
        )

        if fall[0] <= ref_date < fall[1]:
            return Season.FALL
        if winter[0] <= ref_date < winter[1]:
            return Season.WINTER
        if spring[0] <= ref_date < spring[1]:
            return Season.SPRING
        return Season.SUMMER


def season_to_date(season, year=None, hemisphere=Hemisphere.NORTH):
    if year is None:
        year = now_local().year
    elif not isinstance(year, int):
        year = year.year

    if hemisphere == Hemisphere.NORTH:
        if season == Season.SPRING:
            return date(day=1, month=3, year=year)
        elif season == Season.FALL:
            return date(day=1, month=9, year=year)
        elif season == Season.WINTER:
            return date(day=1, month=12, year=year)
        elif season == Season.SUMMER:
            return date(day=1, month=6, year=year)
    else:
        if season == Season.SPRING:
            return date(day=1, month=9, year=year)
        elif season == Season.FALL:
            return date(day=1, month=3, year=year)
        elif season == Season.WINTER:
            return date(day=1, month=6, year=year)
        elif season == Season.SUMMER:
            return date(day=1, month=12, year=year)
    raise ValueError("Unknown Season")


def next_season_date(season, ref_date=None, hemisphere=Hemisphere.NORTH):
    ref_date = ref_date or now_local().date()
    start_day = season_to_date(season, ref_date, hemisphere) \
        .timetuple().tm_yday
    # get the current day of the year
    doy = ref_date.timetuple().tm_yday

    if doy <= start_day:
        # season is this year
        return season_to_date(season, ref_date, hemisphere)
    else:
        # season is next year
        ref_date = ref_date.replace(year=ref_date.year + 1)
        return season_to_date(season, ref_date, hemisphere)


def last_season_date(season, ref_date=None, hemisphere=Hemisphere.NORTH):
    ref_date = ref_date or now_local().date()

    start_day = season_to_date(season, ref_date, hemisphere)\
        .timetuple().tm_yday
    # get the current day of the year
    doy = ref_date.timetuple().tm_yday

    if doy <= start_day:
        # season is previous year
        ref_date = ref_date.replace(year=ref_date.year - 1)
        return season_to_date(season, ref_date, hemisphere)
    else:
        # season is this year
        return season_to_date(season, ref_date, hemisphere)


def get_season_range(ref_date=None, hemisphere=Hemisphere.NORTH):
    ref_date = ref_date or now_local().date()
    if hemisphere == Hemisphere.NORTH:
        fall = (
            date(day=1, month=9, year=ref_date.year),
            date(day=30, month=11, year=ref_date.year)
        )
        spring = (
            date(day=1, month=3, year=ref_date.year),
            date(day=31, month=5, year=ref_date.year)
        )
        summer = (
            date(day=1, month=6, year=ref_date.year),
            date(day=31, month=8, year=ref_date.year)
        )
        early_winter = (
            date(day=1, month=12, year=ref_date.year),
            date(day=28, month=2, year=ref_date.year + 1)
        )
        winter = (
            date(day=1, month=12, year=ref_date.year - 1),
            date(day=28, month=2, year=ref_date.year)
        )

        if fall[0] <= ref_date < fall[1]:
            return fall
        if summer[0] <= ref_date < summer[1]:
            return summer
        if spring[0] <= ref_date < spring[1]:
            return spring
        if early_winter[0] <= ref_date < early_winter[1]:
            return early_winter
        return winter

    else:
        spring = (
            date(day=1, month=9, year=ref_date.year),
            date(day=30, month=11, year=ref_date.year)
        )
        fall = (
            date(day=1, month=3, year=ref_date.year),
            date(day=31, month=5, year=ref_date.year)
        )
        winter = (
            date(day=1, month=6, year=ref_date.year),
            date(day=31, month=8, year=ref_date.year)
        )
        early_summer = (
            date(day=1, month=12, year=ref_date.year),
            date(day=28, month=2, year=ref_date.year + 1)
        )
        summer = (
            date(day=1, month=12, year=ref_date.year - 1),
            date(day=28, month=2, year=ref_date.year)
        )

        if fall[0] <= ref_date < fall[1]:
            return fall
        if winter[0] <= ref_date < winter[1]:
            return winter
        if spring[0] <= ref_date < spring[1]:
            return spring
        if early_summer[0] <= ref_date < early_summer[1]:
            return early_summer
        return summer


if __name__ == "__main__":
    def test_north_hemi():
        start_spring = date(day=1, month=3, year=2117)
        start_summer = date(day=1, month=6, year=2117)
        start_fall = date(day=1, month=9, year=2117)
        start_winter = date(day=1, month=12, year=2117)

        end_spring = date(day=31, month=5, year=2117)
        end_summer = date(day=31, month=8, year=2117)
        end_fall = date(day=30, month=11, year=2117)
        end_winter = date(day=28, month=2, year=2118)

        spring = date(day=20, month=4, year=2117)
        summer = date(day=20, month=8, year=2117)
        fall = date(day=20, month=10, year=2117)
        winter = date(day=30, month=12, year=2117)
        late_winter = date(day=20, month=2, year=2118)

        hemi = Hemisphere.NORTH

        def _test_range(test_date, expected_start, expect_end):
            print("start      |  end")
            print(expected_start, "-", expect_end)
            start, end = get_season_range(test_date, hemi)
            print(start, "-", end)
            assert start == expected_start
            assert end == expect_end

        _test_range(spring, start_spring, end_spring)

        _test_range(fall, start_fall, end_fall)

        _test_range(summer, start_summer, end_summer)

        _test_range(winter, start_winter, end_winter)

        _test_range(late_winter, start_winter, end_winter)


    def test_south_hemi():
        start_spring = date(day=1, month=9, year=2117)
        start_summer = date(day=1, month=12, year=2117)
        start_fall = date(day=1, month=3, year=2117)
        start_winter = date(day=1, month=6, year=2117)

        end_spring = date(day=30, month=11, year=2117)
        end_winter = date(day=31, month=8, year=2117)
        end_fall = date(day=31, month=5, year=2117)
        end_summer = date(day=28, month=2, year=2118)

        fall = date(day=20, month=4, year=2117)
        winter = date(day=20, month=8, year=2117)
        spring = date(day=20, month=10, year=2117)
        summer = date(day=30, month=12, year=2117)
        late_summer = date(day=20, month=2, year=2118)

        hemi = Hemisphere.SOUTH

        def _test_range(test_date, expected_start, expect_end):
            print("start      |  end")
            print(expected_start, "-", expect_end)
            start, end = get_season_range(test_date, hemi)
            print(start, "-", end)
            assert start == expected_start
            assert end == expect_end

        _test_range(spring, start_spring, end_spring)

        _test_range(fall, start_fall, end_fall)

        _test_range(winter, start_winter, end_winter)

        _test_range(summer, start_summer, end_summer)

        _test_range(late_summer, start_summer, end_summer)


    test_north_hemi()
    test_south_hemi()
