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

"""Unit tests for ovos_utils.dialog module."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock


class TestMustacheDialogRenderer(unittest.TestCase):
    """Tests for MustacheDialogRenderer class."""

    def test_render_missing_template_returns_name(self) -> None:
        """render should return the template name (with dots replaced) when not found."""
        from ovos_utils.dialog import MustacheDialogRenderer
        r = MustacheDialogRenderer()
        result = r.render("record.not.found")
        self.assertEqual(result, "record not found")

    def test_load_and_render_basic(self) -> None:
        """load_template_file and render should work for a simple dialog file."""
        from ovos_utils.dialog import MustacheDialogRenderer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dialog",
                                         delete=False) as f:
            f.write("Hello world\n")
            fname = f.name
        try:
            r = MustacheDialogRenderer()
            r.load_template_file("greeting", fname)
            result = r.render("greeting")
            self.assertEqual(result, "Hello world")
        finally:
            os.unlink(fname)

    def test_load_skips_comments_and_blank_lines(self) -> None:
        """load_template_file should skip lines starting with '#' and blank lines."""
        from ovos_utils.dialog import MustacheDialogRenderer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dialog",
                                         delete=False) as f:
            f.write("# comment\n\nHello\n")
            fname = f.name
        try:
            r = MustacheDialogRenderer()
            r.load_template_file("t", fname)
            self.assertEqual(r.templates["t"], ["Hello"])
        finally:
            os.unlink(fname)

    def test_render_with_context(self) -> None:
        """render should substitute context variables using mustache syntax."""
        from ovos_utils.dialog import MustacheDialogRenderer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dialog",
                                         delete=False) as f:
            f.write("Hello {{name}}\n")
            fname = f.name
        try:
            r = MustacheDialogRenderer()
            r.load_template_file("greet", fname)
            result = r.render("greet", context={"name": "OVOS"})
            self.assertEqual(result, "Hello OVOS")
        finally:
            os.unlink(fname)

    def test_render_with_index(self) -> None:
        """render with explicit index should pick the correct template line."""
        from ovos_utils.dialog import MustacheDialogRenderer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dialog",
                                         delete=False) as f:
            f.write("Line A\nLine B\nLine C\n")
            fname = f.name
        try:
            r = MustacheDialogRenderer()
            r.load_template_file("multi", fname)
            result = r.render("multi", index=1)
            self.assertEqual(result, "Line B")
        finally:
            os.unlink(fname)

    def test_render_populates_recent_phrases(self) -> None:
        """render should track recent phrases to avoid repetition."""
        from ovos_utils.dialog import MustacheDialogRenderer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dialog",
                                         delete=False) as f:
            f.write("A\nB\nC\nD\n")
            fname = f.name
        try:
            r = MustacheDialogRenderer()
            r.load_template_file("phrases", fname)
            for _ in range(6):
                r.render("phrases")
            # recent_phrases should not grow beyond max_recent_phrases
            self.assertLessEqual(len(r.recent_phrases), r.max_recent_phrases)
        finally:
            os.unlink(fname)


class TestLoadDialogs(unittest.TestCase):
    """Tests for load_dialogs function."""

    def test_load_from_directory(self) -> None:
        """load_dialogs should load all .dialog files from a directory."""
        from ovos_utils.dialog import load_dialogs, MustacheDialogRenderer
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog_file = os.path.join(tmpdir, "greeting.dialog")
            with open(dialog_file, "w") as f:
                f.write("Hi there\n")
            renderer = load_dialogs(tmpdir)
        self.assertIsInstance(renderer, MustacheDialogRenderer)
        self.assertIn("greeting", renderer.templates)

    def test_load_missing_directory_returns_renderer(self) -> None:
        """load_dialogs should return an empty renderer for a non-existent dir."""
        from ovos_utils.dialog import load_dialogs, MustacheDialogRenderer
        renderer = load_dialogs("/nonexistent/path/dialog")
        self.assertIsInstance(renderer, MustacheDialogRenderer)
        self.assertEqual(renderer.templates, {})

    def test_load_with_existing_renderer(self) -> None:
        """load_dialogs should populate an existing renderer when passed."""
        from ovos_utils.dialog import load_dialogs, MustacheDialogRenderer
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog_file = os.path.join(tmpdir, "bye.dialog")
            with open(dialog_file, "w") as f:
                f.write("Goodbye\n")
            existing = MustacheDialogRenderer()
            result = load_dialogs(tmpdir, renderer=existing)
        self.assertIs(result, existing)
        self.assertIn("bye", result.templates)

    def test_load_ignores_non_dialog_files(self) -> None:
        """load_dialogs should ignore files that do not end with .dialog."""
        from ovos_utils.dialog import load_dialogs
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "readme.txt"), "w") as f:
                f.write("not a dialog\n")
            renderer = load_dialogs(tmpdir)
        self.assertEqual(renderer.templates, {})


class TestGetDialog(unittest.TestCase):
    """Tests for get_dialog function."""

    def test_get_dialog_returns_phrase_when_no_file(self) -> None:
        """get_dialog should return the phrase itself when no resource file found."""
        from ovos_utils.dialog import get_dialog
        with patch("ovos_utils.dialog.resolve_resource_file", return_value=None):
            result = get_dialog("hello.world", lang="en-us")
        self.assertEqual(result, "hello.world")

    def test_get_dialog_returns_rendered_content(self) -> None:
        """get_dialog should load and render template when resource file found."""
        from ovos_utils.dialog import get_dialog
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dialog",
                                         delete=False) as f:
            f.write("Hello from dialog\n")
            fname = f.name
        try:
            with patch("ovos_utils.dialog.resolve_resource_file",
                       return_value=fname):
                result = get_dialog("greeting", lang="en-us")
            self.assertEqual(result, "Hello from dialog")
        finally:
            os.unlink(fname)

    def test_get_dialog_none_lang_uses_config(self) -> None:
        """get_dialog with lang=None should try to read config for language."""
        from ovos_utils.dialog import get_dialog
        with patch("ovos_utils.dialog.resolve_resource_file", return_value=None):
            with patch("ovos_utils.dialog.log_deprecation"):
                # Should not raise even when ovos_config is absent
                result = get_dialog("my.phrase", lang=None)
        self.assertEqual(result, "my.phrase")

    def test_get_dialog_none_lang_config_import_error(self) -> None:
        """get_dialog with lang=None should fall back to en-us on ImportError."""
        from ovos_utils.dialog import get_dialog
        with patch("ovos_utils.dialog.resolve_resource_file", return_value=None):
            with patch("ovos_utils.dialog.log_deprecation"):
                with patch.dict("sys.modules", {"ovos_config": None}):
                    # ImportError path — falls back gracefully
                    result = get_dialog("test", lang=None)
        self.assertEqual(result, "test")


class TestJoinList(unittest.TestCase):
    """Tests for join_list function."""

    def test_empty_list(self) -> None:
        """join_list with empty list should return empty string."""
        from ovos_utils.dialog import join_list
        result = join_list([], "and")
        self.assertEqual(result, "")

    def test_single_item(self) -> None:
        """join_list with one item should return that item as string."""
        from ovos_utils.dialog import join_list
        result = join_list(["apple"], "and")
        self.assertEqual(result, "apple")

    def test_multiple_items(self) -> None:
        """join_list with multiple items should join with comma and connector."""
        from ovos_utils.dialog import join_list
        result = join_list(["a", "b", "c"], "and", lang="en-us")
        self.assertIn("a", result)
        self.assertIn("c", result)

    def test_custom_separator(self) -> None:
        """join_list with custom sep should use it between items."""
        from ovos_utils.dialog import join_list
        result = join_list(["a", "b", "c"], "or", sep=";", lang="en-us")
        self.assertIn(";", result)


if __name__ == "__main__":
    unittest.main()
