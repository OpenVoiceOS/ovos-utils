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
import time
import unittest

from ovos_utils.decorators import classproperty, timed_lru_cache


class TestClassProperty(unittest.TestCase):
    def test_basic_classproperty(self) -> None:
        class MyClass:
            _value = 42

            @classproperty
            def value(cls) -> int:
                return cls._value

        self.assertEqual(MyClass.value, 42)

    def test_classproperty_from_instance(self) -> None:
        class MyClass:
            @classproperty
            def name(cls) -> str:
                return "MyClass"

        obj = MyClass()
        self.assertEqual(obj.name, "MyClass")

    def test_classproperty_subclass(self) -> None:
        class Base:
            _x = 10

            @classproperty
            def x(cls) -> int:
                return cls._x

        class Child(Base):
            _x = 20

        self.assertEqual(Base.x, 10)
        self.assertEqual(Child.x, 20)


class TestTimedLruCache(unittest.TestCase):
    def test_basic_caching(self) -> None:
        call_count = 0

        @timed_lru_cache(seconds=60)
        def expensive(n: int) -> int:
            nonlocal call_count
            call_count += 1
            return n * 2

        self.assertEqual(expensive(5), 10)
        self.assertEqual(expensive(5), 10)
        self.assertEqual(call_count, 1)  # cached second call

    def test_different_args_not_cached(self) -> None:
        call_count = 0

        @timed_lru_cache(seconds=60)
        def fn(n: int) -> int:
            nonlocal call_count
            call_count += 1
            return n

        fn(1)
        fn(2)
        self.assertEqual(call_count, 2)

    def test_cache_expiry(self) -> None:
        call_count = 0

        @timed_lru_cache(seconds=0)
        def fn(n: int) -> int:
            nonlocal call_count
            call_count += 1
            return n

        fn(1)
        time.sleep(0.01)
        fn(1)
        self.assertGreaterEqual(call_count, 2)

    def test_cache_info_available(self) -> None:
        @timed_lru_cache(seconds=60)
        def fn(n: int) -> int:
            return n

        fn(1)
        info = fn.cache_info()
        self.assertIsNotNone(info)

    def test_cache_clear(self) -> None:
        call_count = 0

        @timed_lru_cache(seconds=60)
        def fn(n: int) -> int:
            nonlocal call_count
            call_count += 1
            return n

        fn(1)
        fn.cache_clear()
        fn(1)
        self.assertEqual(call_count, 2)

    def test_decorator_without_args(self) -> None:
        """Calling @timed_lru_cache without parentheses."""
        call_count = 0

        @timed_lru_cache
        def fn(n: int) -> int:
            nonlocal call_count
            call_count += 1
            return n * 3

        self.assertEqual(fn(4), 12)
        self.assertEqual(fn(4), 12)
        self.assertEqual(call_count, 1)


if __name__ == "__main__":
    unittest.main()
