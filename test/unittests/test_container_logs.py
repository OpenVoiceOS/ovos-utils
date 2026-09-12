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

"""Unit tests for ovos_utils.container_logs module."""

import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import patch

from ovos_utils.container_logs import (categorize_container_name,
                                      find_container_binary,
                                      list_container_names,
                                      start_container_log_bridges,
                                      stop_container_log_bridges)


class TestCategorizeContainerName(unittest.TestCase):
    """Tests for the container name to log category mapping."""

    def test_skill_containers_map_to_skills(self) -> None:
        """Every ovos_skill_* container maps to the shared skills category,
        matching how every skill shares one skills.log on a normal install."""
        for name in ("ovos_skill_alarm_ovos_skill", "ovos_skill-podcast",
                     "Ovos_Skill_Count_OpenVoiceOS"):
            self.assertEqual(categorize_container_name(name), "skills")

    def test_core_container_maps_to_skills(self) -> None:
        """The core container's content (intent service handling) is what
        already lands in skills.log on a normal install."""
        self.assertEqual(categorize_container_name("ovos_core"), "skills")

    def test_fixed_service_containers(self) -> None:
        self.assertEqual(categorize_container_name("ovos_audio"), "audio")
        self.assertEqual(categorize_container_name("ovos_listener"), "voice")
        self.assertEqual(categorize_container_name("ovos_messagebus"), "bus")

    def test_phal_containers_map_to_phal(self) -> None:
        for name in ("ovos_phal", "ovos_phal_plugin_bluetooth"):
            self.assertEqual(categorize_container_name(name), "phal")

    def test_gui_containers_map_to_gui(self) -> None:
        self.assertEqual(categorize_container_name("ovos_gui"), "gui")

    def test_skill_prefix_wins_over_later_rules(self) -> None:
        """The skill prefix rule fires first, matching andlo's tested
        reference: a skill container goes to the shared skills category
        even when its name also contains another marker."""
        self.assertEqual(categorize_container_name("ovos_skill_gui"), "skills")

    def test_unknown_containers_map_to_other(self) -> None:
        for name in ("hivemind_bridge", "nginx", "redis"):
            self.assertEqual(categorize_container_name(name), "other")


class TestFindContainerBinary(unittest.TestCase):
    """Tests for docker/podman binary detection."""

    def test_docker_found(self) -> None:
        ok = subprocess.CompletedProcess(["docker", "ps"], 0)
        with patch("ovos_utils.container_logs.subprocess.run",
                   return_value=ok):
            self.assertEqual(find_container_binary(), "docker")

    def test_podman_used_when_docker_fails(self) -> None:
        fail = subprocess.CompletedProcess(["docker", "ps"], 1)
        ok = subprocess.CompletedProcess(["podman", "ps"], 0)
        with patch("ovos_utils.container_logs.subprocess.run",
                   side_effect=[fail, ok]):
            self.assertEqual(find_container_binary(), "podman")

    def test_none_when_neither_works(self) -> None:
        fail = subprocess.CompletedProcess([], 1)
        missing = FileNotFoundError("nope")
        with patch("ovos_utils.container_logs.subprocess.run",
                   side_effect=[missing, fail]):
            self.assertIsNone(find_container_binary())


class TestListContainerNames(unittest.TestCase):
    """Tests for OVOS/HiveMind container discovery."""

    def test_filters_to_ovos_and_hivemind(self) -> None:
        ok = subprocess.CompletedProcess(
            [], 0,
            stdout="ovos_core\novos_audio\nnginx\nredis\nHiveMind-Bridge\n\n")
        with patch("ovos_utils.container_logs.find_container_binary",
                   return_value="docker"), \
             patch("ovos_utils.container_logs.subprocess.run",
                   return_value=ok):
            self.assertEqual(list_container_names(),
                             ["HiveMind-Bridge", "ovos_audio", "ovos_core"])

    def test_no_runtime_returns_empty(self) -> None:
        with patch("ovos_utils.container_logs.find_container_binary",
                   return_value=None):
            self.assertEqual(list_container_names(), [])

    def test_runtime_error_returns_empty(self) -> None:
        fail = subprocess.CompletedProcess([], 1)
        with patch("ovos_utils.container_logs.find_container_binary",
                   return_value="docker"), \
             patch("ovos_utils.container_logs.subprocess.run",
                   return_value=fail):
            self.assertEqual(list_container_names(), [])


class TestContainerLogBridges(unittest.TestCase):
    """Tests for starting and stopping the log bridge subprocesses."""

    def test_start_returns_empty_without_runtime(self) -> None:
        with patch("ovos_utils.container_logs.find_container_binary",
                   return_value=None):
            self.assertEqual(
                start_container_log_bridges(["ovos_core"], Path("/tmp")), [])

    def test_start_bridges_append_to_shared_category_files(self) -> None:
        """Multiple containers of one category each get their own process,
        but all append to the same shared file."""
        procs = [self._fake_proc(), self._fake_proc()]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            with patch("ovos_utils.container_logs.find_container_binary",
                       return_value="docker"), \
                 patch("ovos_utils.container_logs.subprocess.Popen",
                       side_effect=procs) as popen:
                handles = start_container_log_bridges(
                    ["ovos_skill_alarm", "ovos_skill_volume"], target)
            self.assertEqual(handles, procs)
            self.assertEqual(popen.call_count, 2)
            for call, name in zip(popen.call_args_list,
                                  ["ovos_skill_alarm", "ovos_skill_volume"]):
                self.assertEqual(call.args[0],
                                 ["docker", "logs", "-f", "--tail", "0", name])
                self.assertEqual(call.kwargs["stderr"], subprocess.STDOUT)
            self.assertTrue((target / "skills.log").exists())

    def test_stop_terminates_then_kills_stuck_process(self) -> None:
        proc = self._fake_proc()
        proc.wait.side_effect = subprocess.TimeoutExpired("docker", 3)
        stop_container_log_bridges([proc])
        proc.terminate.assert_called_once_with()
        proc.kill.assert_called_once_with()

    def test_stop_skips_already_exited_process(self) -> None:
        proc = self._fake_proc()
        proc.poll.return_value = 0
        stop_container_log_bridges([proc])
        proc.terminate.assert_not_called()

    def test_stop_never_raises_on_dead_process(self) -> None:
        proc = self._fake_proc()
        proc.terminate.side_effect = OSError("already dead")
        proc.wait.side_effect = OSError("already dead")
        stop_container_log_bridges([proc])

    @staticmethod
    def _fake_proc():
        proc = unittest.mock.MagicMock(spec=subprocess.Popen)
        proc.poll.return_value = None
        return proc


if __name__ == "__main__":
    unittest.main()
