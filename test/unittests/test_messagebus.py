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

"""Unit tests for the deprecated ovos_utils.messagebus module."""

import sys
import unittest
import warnings


class TestMessagebus(unittest.TestCase):
    """Tests for deprecated messagebus module imports."""

    def test_import_emits_deprecation_warning(self) -> None:
        """Importing ovos_utils.messagebus should emit a DeprecationWarning."""
        # Remove cached module to force a fresh import
        sys.modules.pop("ovos_utils.messagebus", None)
        with self.assertWarns(DeprecationWarning):
            import ovos_utils.messagebus  # noqa: F401

    def test_fakebus_symbols_re_exported(self) -> None:
        """The messagebus module should re-export FakeBus and Message."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            sys.modules.pop("ovos_utils.messagebus", None)
            import ovos_utils.messagebus as mb
        self.assertTrue(hasattr(mb, "FakeBus"))
        self.assertTrue(hasattr(mb, "Message"))
