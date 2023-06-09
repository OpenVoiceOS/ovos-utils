import unittest
from os.path import expanduser
from dateutil.tz import tzlocal, tzfile, gettz
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from ovos_utils.time import get_config_tz as _get_config_tz
from ovos_utils.time import (
    now_utc,
    now_local,
    to_local,
    to_system,
    to_utc,
    is_leap_year,
    get_next_leap_year
)


# South Africa has no DST, easier to work with
class TestTimeUtils(unittest.TestCase):
    def test_get_tz_default_config(self):
        timezone = _get_config_tz()
        self.assertIsInstance(timezone, tzfile)
    
    @patch("ovos_config.locale.get_config_tz")
    def test_get_tz_user_config(self, mock_tz):
        mock_tz.return_value = gettz("Africa/Johannesburg")
        self.assertIn("Johannesburg", _get_config_tz()._filename)
    
    def test_now_utc(self):
        utc_now = now_utc()
        self.assertIsInstance(utc_now, datetime)
        self.assertEqual(utc_now.utcoffset().total_seconds(), 0)

    @patch("ovos_config.locale.get_config_tz")
    def test_to_utc(self, mock_tz):
        mock_tz.return_value = gettz("Africa/Johannesburg")
        sa_now = datetime.now(gettz("Africa/Johannesburg"))
        utc_now = to_utc(sa_now)
        self.assertIsInstance(utc_now, datetime)
        self.assertEqual(utc_now.utcoffset().total_seconds(), 0)
        self.assertAlmostEqual(sa_now.utcoffset() - utc_now.utcoffset(),
                               timedelta(hours=2),
                               delta=timedelta(minutes=1))
        # w/o tz
        utc_now = to_utc(sa_now.replace(tzinfo=None))
        self.assertAlmostEqual(sa_now.utcoffset() - utc_now.utcoffset(),
                               timedelta(hours=2),
                               delta=timedelta(minutes=1))
    
    @patch("ovos_config.locale.get_config_tz")
    def test_now_local(self, mock_tz):
        mock_tz.return_value = gettz("Africa/Johannesburg")
        local_now = now_local(gettz("Africa/Johannesburg"))
        self.assertIsInstance(local_now, datetime)
        self.assertAlmostEqual(local_now, 
                               datetime.now(gettz("Africa/Johannesburg")),
                               delta=timedelta(minutes=1))
        # w/o tz
        local_now = now_local()
        self.assertAlmostEqual(local_now, 
                               datetime.now(gettz("Africa/Johannesburg")),
                               delta=timedelta(minutes=1))

    @patch("ovos_config.locale.get_config_tz")
    def test_to_local(self, mock_tz):
        mock_tz.return_value = gettz("UTC")
        now_sa = datetime.now(gettz("Africa/Johannesburg"))
        localized = to_local(now_sa)
        self.assertIsInstance(localized, datetime)
        self.assertAlmostEqual(now_sa.utcoffset() - localized.utcoffset(),
                               timedelta(hours=2),
                               delta=timedelta(minutes=1))

        # w/o tzinfo
        now_sa = datetime.now(gettz("Africa/Johannesburg"))
        localized = to_local(now_sa.replace(tzinfo=None))
        self.assertIsInstance(localized, datetime)
        self.assertEqual(localized.utcoffset().total_seconds(), 0)
    
    @patch("ovos_config.locale.get_config_tz")
    def test_to_system(self, mock_tz):
        mock_tz.return_value = gettz("Africa/Johannesburg")
        now_sa = datetime.now(gettz("Africa/Johannesburg"))
        now_sys = to_system(now_sa)
        self.assertIsInstance(now_sys, datetime)
        self.assertAlmostEqual(now_sys, datetime.now(tzlocal()),
                               delta=timedelta(minutes=1))
        # w/o tzinfo
        now_sys = to_system(now_sa.replace(tzinfo=None))
        self.assertIsInstance(now_sys, datetime)
        self.assertAlmostEqual(now_sys, datetime.now(tzlocal()),
                               delta=timedelta(minutes=1))

    def test_is_leap_year(self):
        self.assertEqual(is_leap_year(2001), False)
        self.assertEqual(is_leap_year(2000), True)

    def test_next_leap_year(self):
        self.assertEqual(get_next_leap_year(2001), 2004)
