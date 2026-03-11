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

"""Additional unit tests for ovos_utils.process_utils module."""

import unittest
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call

if TYPE_CHECKING:
    from ovos_utils.process_utils import ProcessStatus


class TestRuntimeRequirements(unittest.TestCase):
    """Tests for RuntimeRequirements dataclass."""

    def test_defaults(self) -> None:
        """RuntimeRequirements should have sensible defaults."""
        from ovos_utils.process_utils import RuntimeRequirements
        req = RuntimeRequirements()
        self.assertTrue(req.network_before_load)
        self.assertTrue(req.internet_before_load)
        self.assertFalse(req.gui_before_load)
        self.assertTrue(req.requires_internet)
        self.assertTrue(req.requires_network)
        self.assertFalse(req.requires_gui)
        self.assertFalse(req.no_internet_fallback)
        self.assertTrue(req.no_gui_fallback)

    def test_custom_values(self) -> None:
        """RuntimeRequirements should accept custom values."""
        from ovos_utils.process_utils import RuntimeRequirements
        req = RuntimeRequirements(
            network_before_load=False,
            internet_before_load=False,
            requires_internet=False,
        )
        self.assertFalse(req.network_before_load)
        self.assertFalse(req.internet_before_load)
        self.assertFalse(req.requires_internet)


class TestProcessState(unittest.TestCase):
    """Tests for ProcessState enum ordering."""

    def test_ordering(self) -> None:
        """ProcessState values should be ordered for easy comparison."""
        from ovos_utils.process_utils import ProcessState
        self.assertGreater(ProcessState.ALIVE, ProcessState.STARTED)
        self.assertGreater(ProcessState.READY, ProcessState.ALIVE)
        self.assertLess(ProcessState.NOT_STARTED, ProcessState.STARTED)


class TestStatusCallbackMap(unittest.TestCase):
    """Tests for StatusCallbackMap namedtuple."""

    def test_defaults_to_none(self) -> None:
        """StatusCallbackMap should default all callbacks to None."""
        from ovos_utils.process_utils import StatusCallbackMap
        cbm = StatusCallbackMap()
        self.assertIsNone(cbm.on_started)
        self.assertIsNone(cbm.on_alive)
        self.assertIsNone(cbm.on_ready)
        self.assertIsNone(cbm.on_error)
        self.assertIsNone(cbm.on_stopping)

    def test_accepts_callbacks(self) -> None:
        """StatusCallbackMap should accept callables."""
        from ovos_utils.process_utils import StatusCallbackMap
        cb = MagicMock()
        cbm = StatusCallbackMap(on_ready=cb)
        self.assertEqual(cbm.on_ready, cb)


class TestProcessStatus(unittest.TestCase):
    """Tests for ProcessStatus state machine."""

    def _make_status(self) -> "ProcessStatus":
        """Build a ProcessStatus with mock callbacks."""
        from ovos_utils.process_utils import ProcessStatus, StatusCallbackMap
        self.on_started = MagicMock()
        self.on_alive = MagicMock()
        self.on_ready = MagicMock()
        self.on_error = MagicMock()
        self.on_stopping = MagicMock()
        cbm = StatusCallbackMap(
            on_started=self.on_started,
            on_alive=self.on_alive,
            on_ready=self.on_ready,
            on_error=self.on_error,
            on_stopping=self.on_stopping,
        )
        return ProcessStatus("test", callback_map=cbm)

    def test_initial_state_is_not_started(self) -> None:
        """ProcessStatus should start in NOT_STARTED state."""
        from ovos_utils.process_utils import ProcessStatus, ProcessState
        ps = ProcessStatus("test")
        self.assertEqual(ps.state, ProcessState.NOT_STARTED)

    def test_set_started(self) -> None:
        """set_started should transition to STARTED and invoke callback."""
        from ovos_utils.process_utils import ProcessState
        ps = self._make_status()
        ps.set_started()
        self.assertEqual(ps.state, ProcessState.STARTED)
        self.on_started.assert_called_once()

    def test_set_alive(self) -> None:
        """set_alive should transition to ALIVE and invoke callback."""
        from ovos_utils.process_utils import ProcessState
        ps = self._make_status()
        ps.set_alive()
        self.assertEqual(ps.state, ProcessState.ALIVE)
        self.on_alive.assert_called_once()

    def test_set_ready(self) -> None:
        """set_ready should transition to READY and invoke callback."""
        from ovos_utils.process_utils import ProcessState
        ps = self._make_status()
        ps.set_ready()
        self.assertEqual(ps.state, ProcessState.READY)
        self.on_ready.assert_called_once()

    def test_set_stopping(self) -> None:
        """set_stopping should transition to STOPPING and invoke callback."""
        from ovos_utils.process_utils import ProcessState
        ps = self._make_status()
        ps.set_stopping()
        self.assertEqual(ps.state, ProcessState.STOPPING)
        self.on_stopping.assert_called_once()

    def test_set_error(self) -> None:
        """set_error should transition to ERROR and invoke callback with message."""
        from ovos_utils.process_utils import ProcessState
        ps = self._make_status()
        ps.set_error("something broke")
        self.assertEqual(ps.state, ProcessState.ERROR)
        self.on_error.assert_called_once_with("something broke")

    def test_check_alive_false_when_not_ready(self) -> None:
        """check_alive should return False when state < ALIVE."""
        ps = self._make_status()
        self.assertFalse(ps.check_alive())

    def test_check_alive_true_when_alive(self) -> None:
        """check_alive should return True when state >= ALIVE."""
        ps = self._make_status()
        ps.set_alive()
        self.assertTrue(ps.check_alive())

    def test_check_ready_false_when_not_ready(self) -> None:
        """check_ready should return False when state < READY."""
        ps = self._make_status()
        ps.set_alive()
        self.assertFalse(ps.check_ready())

    def test_check_ready_true_when_ready(self) -> None:
        """check_ready should return True when state == READY."""
        ps = self._make_status()
        ps.set_ready()
        self.assertTrue(ps.check_ready())

    def test_check_alive_responds_to_bus_message(self) -> None:
        """check_alive should emit a response message when given a bus message."""
        ps = self._make_status()
        ps.set_alive()
        mock_bus = MagicMock()
        ps.bus = mock_bus
        mock_msg = MagicMock()
        mock_msg.response.return_value = MagicMock()
        ps.check_alive(mock_msg)
        mock_msg.response.assert_called_once_with(data={"status": True})
        mock_bus.emit.assert_called_once()

    def test_check_ready_responds_to_bus_message(self) -> None:
        """check_ready should emit a response message when given a bus message."""
        ps = self._make_status()
        ps.set_ready()
        mock_bus = MagicMock()
        ps.bus = mock_bus
        mock_msg = MagicMock()
        mock_msg.response.return_value = MagicMock()
        ps.check_ready(mock_msg)
        mock_msg.response.assert_called_once_with(data={"status": True})
        mock_bus.emit.assert_called_once()

    def test_bind_registers_bus_handlers(self) -> None:
        """bind should register is_alive and is_ready handlers on the bus."""
        from ovos_utils.process_utils import ProcessStatus
        mock_bus = MagicMock()
        ps = ProcessStatus("myproc", bus=mock_bus, namespace="ovos")
        # Should have registered handlers
        calls = [c[0][0] for c in mock_bus.on.call_args_list]
        self.assertIn("ovos.myproc.is_alive", calls)
        self.assertIn("ovos.myproc.is_ready", calls)

    def test_no_callback_set_started(self) -> None:
        """set_started without callbacks should not raise."""
        from ovos_utils.process_utils import ProcessStatus
        ps = ProcessStatus("test")
        ps.set_started()  # should not raise

    def test_no_callback_set_error(self) -> None:
        """set_error without callbacks should not raise."""
        from ovos_utils.process_utils import ProcessStatus
        ps = ProcessStatus("test")
        ps.set_error("err")  # should not raise


if __name__ == "__main__":
    unittest.main()
