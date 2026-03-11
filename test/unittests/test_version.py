# Copyright 2024, OpenVoiceOS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for ovos_utils.version module."""

import unittest


class TestVersion(unittest.TestCase):
    """Tests for the version module constants and string."""

    def test_version_constants_exist(self) -> None:
        """Verify VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD, VERSION_ALPHA are defined."""
        from ovos_utils.version import (
            VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD, VERSION_ALPHA
        )
        self.assertIsInstance(VERSION_MAJOR, int)
        self.assertIsInstance(VERSION_MINOR, int)
        self.assertIsInstance(VERSION_BUILD, int)
        self.assertIsInstance(VERSION_ALPHA, int)

    def test_dunder_version_is_string(self) -> None:
        """Verify __version__ is a string."""
        from ovos_utils.version import __version__
        self.assertIsInstance(__version__, str)

    def test_dunder_version_format(self) -> None:
        """Verify __version__ starts with major.minor.build."""
        from ovos_utils.version import (
            VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD, __version__
        )
        expected_prefix = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}"
        self.assertTrue(__version__.startswith(expected_prefix))

    def test_dunder_version_alpha_suffix(self) -> None:
        """Verify alpha suffix is appended when VERSION_ALPHA is non-zero."""
        from ovos_utils.version import (
            VERSION_ALPHA, __version__
        )
        if VERSION_ALPHA:
            self.assertIn(f"a{VERSION_ALPHA}", __version__)
        else:
            self.assertNotIn("a", __version__)


if __name__ == "__main__":
    unittest.main()
