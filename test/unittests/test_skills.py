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

"""Unit tests for ovos_utils.skills module."""

import unittest
from unittest.mock import MagicMock, patch


class TestGetNonProperties(unittest.TestCase):
    """Tests for the get_non_properties helper function."""

    def test_returns_set(self) -> None:
        """get_non_properties should return a set."""
        from ovos_utils.skills import get_non_properties

        class SimpleClass:
            def regular_method(self):
                pass

            @property
            def my_prop(self):
                return 1

        result = get_non_properties(SimpleClass())
        self.assertIsInstance(result, set)

    def test_excludes_properties(self) -> None:
        """Properties should not appear in the returned set."""
        from ovos_utils.skills import get_non_properties

        class WithProp:
            @property
            def prop_val(self):
                return 42

            def regular(self):
                pass

        result = get_non_properties(WithProp())
        self.assertNotIn("prop_val", result)
        self.assertIn("regular", result)

    def test_includes_inherited_non_properties(self) -> None:
        """Methods from base classes should be included (unless named object/MycroftSkill)."""
        from ovos_utils.skills import get_non_properties

        class Base:
            def base_method(self):
                pass

        class Child(Base):
            def child_method(self):
                pass

        result = get_non_properties(Child())
        self.assertIn("child_method", result)
        self.assertIn("base_method", result)

    def test_skips_mycroft_skill_base(self) -> None:
        """MycroftSkill base class methods should be excluded from recursion."""
        from ovos_utils.skills import get_non_properties

        class MycroftSkill:
            def mycroft_method(self):
                pass

        class MySkill(MycroftSkill):
            def my_method(self):
                pass

        result = get_non_properties(MySkill())
        self.assertIn("my_method", result)
        self.assertNotIn("mycroft_method", result)


class TestSkillsLoaded(unittest.TestCase):
    """Tests for the skills_loaded function."""

    def test_returns_false_when_bus_is_none(self) -> None:
        """skills_loaded should return False when no bus is provided."""
        from ovos_utils.skills import skills_loaded
        result = skills_loaded(bus=None)
        self.assertFalse(result)

    def test_returns_false_when_no_reply(self) -> None:
        """skills_loaded should return False when wait_for_reply returns None."""
        from ovos_utils.skills import skills_loaded
        with patch("ovos_utils.skills.wait_for_reply", return_value=None):
            fake_bus = MagicMock()
            result = skills_loaded(bus=fake_bus)
            self.assertFalse(result)

    def test_returns_status_from_reply(self) -> None:
        """skills_loaded should return the status field from a successful reply."""
        from ovos_utils.skills import skills_loaded
        mock_reply = MagicMock()
        mock_reply.data = {"status": True}
        with patch("ovos_utils.skills.wait_for_reply", return_value=mock_reply):
            fake_bus = MagicMock()
            result = skills_loaded(bus=fake_bus)
            self.assertTrue(result)

    def test_returns_false_status_from_reply(self) -> None:
        """skills_loaded should return False when reply status is False."""
        from ovos_utils.skills import skills_loaded
        mock_reply = MagicMock()
        mock_reply.data = {"status": False}
        with patch("ovos_utils.skills.wait_for_reply", return_value=mock_reply):
            fake_bus = MagicMock()
            result = skills_loaded(bus=fake_bus)
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
