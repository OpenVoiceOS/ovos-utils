# Copyright 2025 OpenVoiceOS
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
"""Unit tests for :class:`~ovos_utils.skill_installer.ServiceInstaller`."""
import sys
from unittest.mock import MagicMock, patch, call

import pytest

from ovos_bus_client import Message
from ovos_utils.skill_installer import InstallError, ServiceInstaller


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

class FakeBus:
    """Minimal in-process bus stub sufficient for unit tests."""

    def __init__(self) -> None:
        self.emitted: list[Message] = []
        self.handlers: dict[str, list] = {}

    def emit(self, message: Message) -> None:
        self.emitted.append(message)

    def on(self, event: str, handler) -> None:
        self.handlers.setdefault(event, []).append(handler)

    def remove(self, event: str, handler) -> None:
        if event in self.handlers and handler in self.handlers[event]:
            self.handlers[event].remove(handler)

    # helpers for assertions
    def last_type(self) -> str:
        return self.emitted[-1].msg_type

    def last_data(self) -> dict:
        return self.emitted[-1].data


@pytest.fixture()
def bus() -> FakeBus:
    return FakeBus()


@pytest.fixture()
def installer(bus: FakeBus) -> ServiceInstaller:
    return ServiceInstaller(bus, service_name="ovos_test", config={"allow_pip": True})


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_broadcast_topics_registered(self, bus: FakeBus) -> None:
        ServiceInstaller(bus, "svc", config={})
        assert "ovos.pip.install" in bus.handlers
        assert "ovos.pip.uninstall" in bus.handlers

    def test_targeted_topics_registered(self, bus: FakeBus) -> None:
        ServiceInstaller(bus, "my_service", config={})
        assert "ovos.pip.install.my_service" in bus.handlers
        assert "ovos.pip.uninstall.my_service" in bus.handlers

    def test_shutdown_removes_all_handlers(self, bus: FakeBus) -> None:
        inst = ServiceInstaller(bus, "svc", config={})
        inst.shutdown()
        assert bus.handlers.get("ovos.pip.install", []) == []
        assert bus.handlers.get("ovos.pip.uninstall", []) == []
        assert bus.handlers.get("ovos.pip.install.svc", []) == []
        assert bus.handlers.get("ovos.pip.uninstall.svc", []) == []


# ---------------------------------------------------------------------------
# Audio feedback
# ---------------------------------------------------------------------------

class TestAudioFeedback:
    def test_play_error_sound_default(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        installer.play_error_sound()
        assert bus.last_type() == "mycroft.audio.play_sound"
        assert bus.last_data() == {"uri": "snd/error.mp3"}

    def test_play_success_sound_default(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        installer.play_success_sound()
        assert bus.last_type() == "mycroft.audio.play_sound"
        assert bus.last_data() == {"uri": "snd/acknowledge.mp3"}

    def test_play_error_sound_custom(self, bus: FakeBus) -> None:
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True, "sounds": {"pip_error": "snd/boom.mp3"}})
        inst.play_error_sound()
        assert bus.last_data() == {"uri": "snd/boom.mp3"}

    def test_play_success_sound_custom(self, bus: FakeBus) -> None:
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True, "sounds": {"pip_success": "snd/yay.mp3"}})
        inst.play_success_sound()
        assert bus.last_data() == {"uri": "snd/yay.mp3"}


# ---------------------------------------------------------------------------
# handle_install_python — pip disabled
# ---------------------------------------------------------------------------

class TestHandleInstallDisabled:
    @pytest.fixture()
    def disabled(self, bus: FakeBus) -> ServiceInstaller:
        return ServiceInstaller(bus, "svc", config={"allow_pip": False})

    def test_emits_failed_when_disabled(self, disabled: ServiceInstaller, bus: FakeBus) -> None:
        msg = Message("ovos.pip.install", {"packages": ["some-pkg"]})
        disabled.handle_install_python(msg)
        assert bus.last_type() == "ovos.pip.install.failed"
        assert bus.last_data()["error"] == InstallError.DISABLED.value

    def test_emits_failed_when_no_packages(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        msg = Message("ovos.pip.install", {})
        installer.handle_install_python(msg)
        assert bus.last_type() == "ovos.pip.install.failed"
        assert bus.last_data()["error"] == InstallError.NO_PKGS.value


# ---------------------------------------------------------------------------
# handle_install_python — success / failure paths
# ---------------------------------------------------------------------------

class TestHandleInstallPython:
    def test_emits_complete_on_success(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        with patch.object(installer, "pip_install", return_value=True):
            msg = Message("ovos.pip.install", {"packages": ["pkg-a"]})
            installer.handle_install_python(msg)
        assert bus.last_type() == "ovos.pip.install.complete"

    def test_emits_failed_on_pip_error(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        with patch.object(installer, "pip_install", side_effect=RuntimeError("fail")):
            msg = Message("ovos.pip.install", {"packages": ["pkg-a"]})
            installer.handle_install_python(msg)
        assert bus.last_type() == "ovos.pip.install.failed"
        assert bus.last_data()["error"] == InstallError.PIP_ERROR.value

    def test_targeted_message_handled(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        with patch.object(installer, "pip_install", return_value=True):
            msg = Message("ovos.pip.install.ovos_test", {"packages": ["pkg-b"]})
            installer.handle_install_python(msg)
        assert bus.last_type() == "ovos.pip.install.complete"


# ---------------------------------------------------------------------------
# handle_uninstall_python
# ---------------------------------------------------------------------------

class TestHandleUninstallPython:
    def test_emits_complete_on_success(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        with patch.object(installer, "pip_uninstall", return_value=True):
            msg = Message("ovos.pip.uninstall", {"packages": ["pkg-a"]})
            installer.handle_uninstall_python(msg)
        assert bus.last_type() == "ovos.pip.uninstall.complete"

    def test_emits_failed_on_pip_error(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        with patch.object(installer, "pip_uninstall", side_effect=RuntimeError("fail")):
            msg = Message("ovos.pip.uninstall", {"packages": ["pkg-a"]})
            installer.handle_uninstall_python(msg)
        assert bus.last_type() == "ovos.pip.uninstall.failed"

    def test_emits_failed_when_no_packages(self, installer: ServiceInstaller, bus: FakeBus) -> None:
        msg = Message("ovos.pip.uninstall", {})
        installer.handle_uninstall_python(msg)
        assert bus.last_type() == "ovos.pip.uninstall.failed"
        assert bus.last_data()["error"] == InstallError.NO_PKGS.value

    def test_disabled_emits_failed(self, bus: FakeBus) -> None:
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": False})
        msg = Message("ovos.pip.uninstall", {"packages": ["pkg"]})
        inst.handle_uninstall_python(msg)
        assert bus.last_type() == "ovos.pip.uninstall.failed"
        assert bus.last_data()["error"] == InstallError.DISABLED.value


# ---------------------------------------------------------------------------
# pip_install — subprocess logic (mocked)
# ---------------------------------------------------------------------------

class TestPipInstall:
    def test_returns_false_when_no_packages(self, installer: ServiceInstaller) -> None:
        result = installer.pip_install([])
        assert result is False

    def test_returns_false_on_bad_constraints(self, installer: ServiceInstaller) -> None:
        with patch.object(ServiceInstaller, "validate_constraints", return_value=False):
            result = installer.pip_install(["pkg"])
        assert result is False

    def test_calls_subprocess_with_uv_when_available(
        self, installer: ServiceInstaller, bus: FakeBus
    ) -> None:
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "UV", "/usr/bin/uv"),
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            result = installer.pip_install(["my-pkg"], constraints="http://example.com/c.txt")
        assert result is True
        args = popen_mock.call_args[0][0]
        assert args[0] == "/usr/bin/uv"
        assert "my-pkg" in args

    def test_calls_subprocess_with_python_when_uv_absent(
        self, installer: ServiceInstaller
    ) -> None:
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "UV", None),
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            installer.pip_install(["my-pkg"], constraints="http://example.com/c.txt")
        args = popen_mock.call_args[0][0]
        assert args[0] == sys.executable

    def test_raises_on_nonzero_exit(self, installer: ServiceInstaller) -> None:
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 1
        proc_mock.stderr = None
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
        ):
            with pytest.raises(RuntimeError):
                installer.pip_install(["bad-pkg"], print_logs=False)

    def test_on_install_complete_called(self, installer: ServiceInstaller) -> None:
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
            patch.object(installer, "_on_install_complete") as hook,
        ):
            installer.pip_install(["pkg"], constraints="http://x.com/c.txt")
        hook.assert_called_once()


# ---------------------------------------------------------------------------
# validate_constraints
# ---------------------------------------------------------------------------

class TestValidateConstraints:
    def test_returns_true_for_existing_file(self, tmp_path) -> None:
        f = tmp_path / "constraints.txt"
        f.write_text("ovos-core==1.0\n")
        assert ServiceInstaller.validate_constraints(str(f)) is True

    def test_returns_false_for_missing_file(self) -> None:
        assert ServiceInstaller.validate_constraints("/nonexistent/path.txt") is False

    def test_returns_true_for_valid_url(self) -> None:
        resp = MagicMock()
        resp.status_code = 200
        with patch("ovos_utils.skill_installer.requests.head", return_value=resp):
            assert ServiceInstaller.validate_constraints("http://example.com/c.txt") is True

    def test_returns_false_for_bad_url(self) -> None:
        resp = MagicMock()
        resp.status_code = 404
        with patch("ovos_utils.skill_installer.requests.head", return_value=resp):
            assert ServiceInstaller.validate_constraints("http://example.com/missing.txt") is False

    def test_returns_false_on_request_exception(self) -> None:
        with patch("ovos_utils.skill_installer.requests.head", side_effect=Exception("timeout")):
            assert ServiceInstaller.validate_constraints("http://example.com/c.txt") is False


# ---------------------------------------------------------------------------
# Extension hooks
# ---------------------------------------------------------------------------

class TestExtensionHooks:
    def test_on_install_complete_is_noop_by_default(self, installer: ServiceInstaller) -> None:
        """Base class hook should not raise."""
        installer._on_install_complete()

    def test_on_uninstall_complete_is_noop_by_default(self, installer: ServiceInstaller) -> None:
        installer._on_uninstall_complete()

    def test_subclass_hook_called_on_install(self, bus: FakeBus) -> None:
        hook_calls = []

        class MyInstaller(ServiceInstaller):
            def _on_install_complete(self) -> None:
                hook_calls.append("install_complete")

        inst = MyInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
        ):
            inst.pip_install(["pkg"], constraints="http://x.com/c.txt")
        assert hook_calls == ["install_complete"]


# ---------------------------------------------------------------------------
# pip_install — break_system_packages and allow_alphas options (lines 230, 232)
# ---------------------------------------------------------------------------

class TestPipInstallOptions:
    """Tests for pip_install config options."""

    def test_break_system_packages_flag(self, bus: FakeBus) -> None:
        """pip_install should pass --break-system-packages when configured."""
        inst = ServiceInstaller(bus, "svc", config={
            "allow_pip": True, "break_system_packages": True
        })
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            inst.pip_install(["pkg"], constraints="http://x.com/c.txt")
        args = popen_mock.call_args[0][0]
        assert "--break-system-packages" in args

    def test_allow_alphas_flag(self, bus: FakeBus) -> None:
        """pip_install should pass --pre when allow_alphas is True."""
        inst = ServiceInstaller(bus, "svc", config={
            "allow_pip": True, "allow_alphas": True
        })
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            inst.pip_install(["pkg"], constraints="http://x.com/c.txt")
        args = popen_mock.call_args[0][0]
        assert "--pre" in args

    def test_print_logs_false_uses_pipe(self, bus: FakeBus) -> None:
        """pip_install with print_logs=False should redirect stdout/stderr to PIPE."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            inst.pip_install(["pkg"], constraints="http://x.com/c.txt",
                             print_logs=False)
        kwargs = popen_mock.call_args[1]
        assert "stdout" in kwargs

    def test_nonzero_exit_with_stderr_raises(self, bus: FakeBus) -> None:
        """pip_install nonzero exit with stderr content should raise RuntimeError."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 1
        proc_mock.stderr.read.return_value = b"some error"
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
        ):
            import pytest as _pytest
            with _pytest.raises(RuntimeError):
                inst.pip_install(["pkg"], constraints="http://x.com/c.txt",
                                 print_logs=False)


# ---------------------------------------------------------------------------
# pip_uninstall (lines 273-343)
# ---------------------------------------------------------------------------

class TestPipUninstall:
    """Tests for pip_uninstall method."""

    def test_returns_false_when_no_packages(self, installer: ServiceInstaller) -> None:
        """pip_uninstall should return False when packages list is empty."""
        result = installer.pip_uninstall([])
        assert result is False

    def test_returns_false_on_bad_constraints(self, installer: ServiceInstaller) -> None:
        """pip_uninstall should return False when constraints fail validation."""
        with patch.object(ServiceInstaller, "validate_constraints", return_value=False):
            result = installer.pip_uninstall(["pkg"])
        assert result is False

    def test_returns_false_for_protected_package(self, installer: ServiceInstaller) -> None:
        """pip_uninstall should refuse to uninstall ovos-core."""
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
        ):
            # ovos-core is in the default protected list
            result = installer.pip_uninstall(["ovos-core"])
        assert result is False

    def test_success_with_uv(self, bus: FakeBus) -> None:
        """pip_uninstall should call uv pip uninstall when UV is available."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "UV", "/usr/bin/uv"),
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            result = inst.pip_uninstall(["custom-pkg"])
        assert result is True
        args = popen_mock.call_args[0][0]
        assert args[0] == "/usr/bin/uv"
        assert "uninstall" in args

    def test_success_without_uv(self, bus: FakeBus) -> None:
        """pip_uninstall should use sys.executable when UV is None."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "UV", None),
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            result = inst.pip_uninstall(["custom-pkg"])
        assert result is True
        args = popen_mock.call_args[0][0]
        assert args[0] == sys.executable

    def test_raises_on_nonzero_exit(self, bus: FakeBus) -> None:
        """pip_uninstall should raise RuntimeError on nonzero subprocess exit."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 1
        proc_mock.stderr.read.return_value = b"uninstall error"
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
        ):
            import pytest as _pytest
            with _pytest.raises(RuntimeError):
                inst.pip_uninstall(["custom-pkg"], print_logs=False)

    def test_reads_constraints_from_url(self, bus: FakeBus) -> None:
        """pip_uninstall should fetch constraints via HTTP when URL is provided."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        import requests as _req
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.requests.get") as mock_get,
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
        ):
            mock_get.return_value.text = "some-package==1.0\n"
            result = inst.pip_uninstall(["custom-pkg"],
                                        constraints="http://example.com/c.txt")
        assert result is True
        mock_get.assert_called_once()

    def test_reads_constraints_from_file(self, bus: FakeBus, tmp_path) -> None:
        """pip_uninstall should read constraints from a local file."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        constraints_file = tmp_path / "constraints.txt"
        constraints_file.write_text("some-package==1.0\n")
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
        ):
            result = inst.pip_uninstall(["custom-pkg"],
                                        constraints=str(constraints_file))
        assert result is True

    def test_break_system_packages_flag(self, bus: FakeBus) -> None:
        """pip_uninstall should pass --break-system-packages when configured."""
        inst = ServiceInstaller(bus, "svc", config={
            "allow_pip": True, "break_system_packages": True
        })
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock) as popen_mock,
        ):
            inst.pip_uninstall(["custom-pkg"])
        args = popen_mock.call_args[0][0]
        assert "--break-system-packages" in args

    def test_on_uninstall_complete_called(self, bus: FakeBus) -> None:
        """pip_uninstall should call _on_uninstall_complete on success."""
        inst = ServiceInstaller(bus, "svc", config={"allow_pip": True})
        proc_mock = MagicMock()
        proc_mock.wait.return_value = 0
        with (
            patch.object(ServiceInstaller, "validate_constraints", return_value=True),
            patch("ovos_utils.skill_installer.Popen", return_value=proc_mock),
            patch.object(inst, "_on_uninstall_complete") as hook,
        ):
            inst.pip_uninstall(["custom-pkg"])
        hook.assert_called_once()
