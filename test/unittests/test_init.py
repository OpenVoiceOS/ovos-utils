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
#
import dataclasses
import unittest
from ovos_utils import json_dumps, json_loads


class TestJsonDumps(unittest.TestCase):
    """Tests for json_dumps / json_loads in ovos_utils/__init__.py"""

    def test_dumps_dict(self) -> None:
        result = json_dumps({"key": "value", "num": 42})
        self.assertIn('"key"', result)
        self.assertIn('"value"', result)
        self.assertIn("42", result)

    def test_dumps_list(self) -> None:
        result = json_dumps([1, 2, 3])
        self.assertEqual(json_loads(result), [1, 2, 3])

    def test_dumps_string(self) -> None:
        result = json_dumps("hello")
        self.assertIn("hello", result)

    def test_dumps_none(self) -> None:
        result = json_dumps(None)
        self.assertEqual(result, "null")

    def test_dumps_bool(self) -> None:
        self.assertIn("true", json_dumps(True).lower())
        self.assertIn("false", json_dumps(False).lower())

    def test_dumps_nested(self) -> None:
        payload = {"a": {"b": [1, 2, 3]}}
        result = json_dumps(payload)
        self.assertEqual(json_loads(result), payload)

    def test_dumps_unicode(self) -> None:
        payload = {"greeting": "héllo wörld"}
        result = json_dumps(payload)
        self.assertIn("héllo", result)

    def test_dumps_dataclass(self) -> None:
        @dataclasses.dataclass
        class Point:
            x: int
            y: int

        p = Point(x=3, y=7)
        result = json_dumps(p)
        loaded = json_loads(result)
        self.assertEqual(loaded["x"], 3)
        self.assertEqual(loaded["y"], 7)

    def test_roundtrip(self) -> None:
        original = {"nested": {"list": [1, "two", 3.0], "bool": True}}
        self.assertEqual(json_loads(json_dumps(original)), original)


class TestJsonLoads(unittest.TestCase):
    """Tests for json_loads in ovos_utils/__init__.py"""

    def test_loads_dict(self) -> None:
        result = json_loads('{"a": 1}')
        self.assertEqual(result, {"a": 1})

    def test_loads_list(self) -> None:
        result = json_loads('[1, 2, 3]')
        self.assertEqual(result, [1, 2, 3])

    def test_loads_null(self) -> None:
        result = json_loads("null")
        self.assertIsNone(result)

    def test_loads_unicode(self) -> None:
        result = json_loads('{"word": "héllo"}')
        self.assertEqual(result["word"], "héllo")


if __name__ == "__main__":
    unittest.main()
