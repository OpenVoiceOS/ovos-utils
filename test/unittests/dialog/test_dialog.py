#
# Copyright 2017 Mycroft AI Inc.
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
#
import unittest
import pathlib
import json
import random

import pytest

from ovos_utils.dialog import MustacheDialogRenderer, load_dialogs, get_dialog

# ovos_utils.dialog is a deprecated shim; this module deliberately keeps
# exercising it for coverage, filtered per-module rather than dropped.
pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:MustacheDialogRenderer is deprecated; use the OVOS-INTENT-2:DeprecationWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:get_dialog is deprecated; use the OVOS-INTENT-2:DeprecationWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:load_dialogs is deprecated; use 'ovos_spec_tools.LocaleResources':DeprecationWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:EventSchedulerInterface moved to ovos_bus_client:DeprecationWarning"
    ),
]


# TODO - move to ovos-workshop
class DialogTest(unittest.TestCase):
    def setUp(self):
        self.stache = MustacheDialogRenderer()
        self.topdir = pathlib.Path(__file__).parent

    def test_general_dialog(self):
        """ Test the loading and filling of valid simple mustache dialogs """
        template_path = self.topdir.joinpath('./mustache_templates')
        for file in template_path.iterdir():
            if file.suffix == '.dialog':
                self.stache.load_template_file(file.name, str(file.absolute()))
                with file.with_suffix('.context.json').open(
                        'r', encoding='utf-8') as f:
                    context = json.load(f)
                with file.with_suffix('.result').open(
                        'r', encoding='utf-8') as f:
                    expected = f.read()
                self.assertEqual(
                    self.stache.render(file.name, context),
                    expected)

    def test_unknown_dialog(self):
        """ Test for returned file name literals in case of unkown dialog """
        self.assertEqual(
            self.stache.render("unknown.template"), "unknown template")

    def test_multiple_dialog(self):
        """
        Test the loading and filling of valid mustache dialogs
        where a dialog file contains multiple text versions
        """
        template_path = self.topdir.joinpath('./mustache_templates_multiple')
        for file in template_path.iterdir():
            if file.suffix == '.dialog':
                self.stache.load_template_file(file.name, str(file.absolute()))
                with file.with_suffix('.context.json').open(
                        'r', encoding='utf-8') as f:
                    context = json.load(f)
                with file.with_suffix('.result').open(
                        'r', encoding='utf-8') as fh:
                    results = [line.strip() for line in fh]
                # Try all lines
                for index, line in enumerate(results):
                    self.assertEqual(
                        self.stache.render(
                            file.name, index=index, context=context),
                        line.strip())
                # Test random index function
                # (bad test because non-deterministic?)
                self.assertIn(
                    self.stache.render(file.name, context=context), results)

    def test_comment_dialog(self):
        """
        Test the loading and filling of valid mustache dialogs
        where a dialog file contains multiple text versions
        """
        template_path = self.topdir.joinpath('./mustache_templates_comments')
        for f in template_path.iterdir():
            if f.suffix == '.dialog':
                self.stache.load_template_file(f.name, str(f.absolute()))
                with f.with_suffix('.result').open('r') as fh:
                    results = [line.strip() for line in fh]
                # Try all lines
                for index, line in enumerate(results):
                    self.assertEqual(self.stache.render(f.name, index=index),
                                     line.strip())

    def test_dialog_loader(self):
        template_path = self.topdir.joinpath('./multiple_dialogs')
        renderer = load_dialogs(template_path)
        self.assertEqual(renderer.render('one'), 'ONE')
        self.assertEqual(renderer.render('two'), 'TWO')

    def test_dialog_loader_missing(self):
        template_path = self.topdir.joinpath('./missing_dialogs')
        renderer = load_dialogs(template_path)
        self.assertEqual(renderer.render('test'), 'test')


    def test_repeat_avoidance_with_slots(self):
        """A template that carries a slot must still be held back.

        The renderer remembers what it said in order to not repeat a line.
        It remembers the unrendered template, because a rendered line never
        equals the template it came from once the template carries a {slot}
        or an (a|b) group.
        """
        cases = {
            "slot_free": (["Hello there",
                           "Another possible outcome",
                           "Oh look at the capabilities"], {}),
            "slot_carrying": (["Hello there {name}!",
                               "Another possible outcome, {name}",
                               "Oh, {name} look at the capabilities"],
                              {"name": "Sherlock"}),
            "alternation_only": (["(Hi|Hello) there",
                                  "(Good|Great) to see you",
                                  "(Welcome|Greetings) friend"], {}),
        }
        for name, (templates, context) in cases.items():
            with self.subTest(case=name):
                random.seed(7)
                renderer = MustacheDialogRenderer()
                renderer.templates["repeat"] = list(templates)
                previous = None
                rendered = set()
                for _ in range(200):
                    line = renderer.render("repeat", context)
                    self.assertNotEqual(
                        line, previous,
                        "{} repeated a line back to back".format(name))
                    previous = line
                    rendered.add(line)
                # the filter must hold lines back, not collapse the choice
                self.assertGreaterEqual(len(rendered), len(templates))

    def test_recent_phrases_holds_templates(self):
        """What is remembered must be comparable to what is filtered."""
        renderer = MustacheDialogRenderer()
        # three lines: with two or fewer, loop_prevention_offset turns the
        # repeat filter off on purpose and nothing is remembered
        renderer.templates["repeat"] = ["Hello there {name}!",
                                        "Goodbye {name}",
                                        "See you {name}"]
        renderer.render("repeat", {"name": "Sherlock"})
        self.assertTrue(renderer.recent_phrases)
        for phrase in renderer.recent_phrases:
            self.assertIn(phrase, renderer.templates["repeat"])


if __name__ == "__main__":
    unittest.main()
