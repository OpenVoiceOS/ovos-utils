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
"""Service-level pip installer.

Provides :class:`ServiceInstaller`, a lightweight class that listens on the
MessageBus for pip install/uninstall requests and executes them in the calling
process's Python environment.

Each OVOS core service (ovos-core, ovos-audio, ovos-gui, ovos-messagebus) runs
in its own process — and potentially its own container.  This module makes it
possible to install or update Python packages in *each* service independently
by targeting messages at a specific service name.

Message protocol
----------------
Broadcast (all services respond)::

    ovos.pip.install          data: {"packages": ["pkg-name"]}
    ovos.pip.uninstall        data: {"packages": ["pkg-name"]}

Targeted (only the named service responds)::

    ovos.pip.install.<service_name>    data: {"packages": ["pkg-name"]}
    ovos.pip.uninstall.<service_name>  data: {"packages": ["pkg-name"]}

Response messages emitted by each handler::

    ovos.pip.install.complete
    ovos.pip.install.failed   data: {"error": <InstallError value>}
    ovos.pip.uninstall.complete
    ovos.pip.uninstall.failed data: {"error": <InstallError value>}

GGWave opcodes (audio-QR)
-------------------------
``PIP:<pkg>``               → broadcast install (all services)
``RMPIP:<pkg>``             → broadcast uninstall (all services)
``SPIP:<service>:<pkg>``    → targeted install to one service
``RMSPIP:<service>:<pkg>``  → targeted uninstall from one service
"""
import enum
import shutil
import sys
from os.path import exists
from subprocess import Popen, PIPE
from typing import List, Optional

import requests
from combo_lock import NamedLock
from ovos_bus_client import Message
from ovos_config.config import Configuration
from ovos_utils.log import LOG


class InstallError(str, enum.Enum):
    """Error codes returned in ``ovos.pip.install.failed`` messages."""

    DISABLED = "pip disabled in mycroft.conf"
    PIP_ERROR = "error in pip subprocess"
    BAD_URL = "skill url validation failed"
    NO_PKGS = "no packages to install"


class ServiceInstaller:
    """Pip installer bound to a single OVOS service process.

    Listens on both the broadcast ``ovos.pip.install`` topic and the
    service-specific ``ovos.pip.install.<service_name>`` topic so that each
    containerised service can be updated independently.

    Args:
        bus: Connected ``MessageBusClient`` (or compatible FakeBus).
        service_name: Logical name of the owning service, used to construct
            the targeted message topic.  Should match the container/process
            name without spaces, e.g. ``"ovos_audio"``, ``"ovos_gui"``,
            ``"ovos_messagebus"``, ``"ovos_core"``.
        config: Optional installer configuration dict.  Falls back to the
            ``skills.installer`` section of ``mycroft.conf`` when omitted.
    """

    # Default constraints URL — same as SkillsStore so all services share
    # the same protection list.
    DEFAULT_CONSTRAINTS: str = (
        "https://raw.githubusercontent.com/OpenVoiceOS/ovos-releases"
        "/refs/heads/main/constraints-stable.txt"
    )
    PIP_LOCK: NamedLock = NamedLock("ovos_pip.lock")
    UV: Optional[str] = shutil.which("uv")  # prefer uv when available

    def __init__(
        self,
        bus,
        service_name: str,
        config: Optional[dict] = None,
    ) -> None:
        self.service_name: str = service_name
        self.config: dict = config or Configuration().get("skills", {}).get(
            "installer", {}
        )
        self.bus = bus

        # Broadcast topics — every service with an installer will respond.
        self.bus.on("ovos.pip.install", self.handle_install_python)
        self.bus.on("ovos.pip.uninstall", self.handle_uninstall_python)

        # Targeted topics — only this service responds.
        self.bus.on(
            f"ovos.pip.install.{self.service_name}",
            self.handle_install_python,
        )
        self.bus.on(
            f"ovos.pip.uninstall.{self.service_name}",
            self.handle_uninstall_python,
        )

        LOG.info(
            f"ServiceInstaller registered for service '{self.service_name}'"
        )

    def shutdown(self) -> None:
        """Unregister all message bus event handlers."""
        self.bus.remove("ovos.pip.install", self.handle_install_python)
        self.bus.remove("ovos.pip.uninstall", self.handle_uninstall_python)
        self.bus.remove(
            f"ovos.pip.install.{self.service_name}",
            self.handle_install_python,
        )
        self.bus.remove(
            f"ovos.pip.uninstall.{self.service_name}",
            self.handle_uninstall_python,
        )

    # ------------------------------------------------------------------
    # Audio feedback helpers
    # ------------------------------------------------------------------

    def play_error_sound(self) -> None:
        """Emit a message to play the configured error sound."""
        snd = self.config.get("sounds", {}).get("pip_error", "snd/error.mp3")
        self.bus.emit(Message("mycroft.audio.play_sound", {"uri": snd}))

    def play_success_sound(self) -> None:
        """Emit a message to play the configured success sound."""
        snd = self.config.get("sounds", {}).get(
            "pip_success", "snd/acknowledge.mp3"
        )
        self.bus.emit(Message("mycroft.audio.play_sound", {"uri": snd}))

    # ------------------------------------------------------------------
    # Constraints validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_constraints(constraints: str) -> bool:
        """Return *True* if the constraints file/URL is accessible.

        Args:
            constraints: Local file path or HTTP URL to a pip constraints file.
        """
        if constraints.startswith("http"):
            LOG.debug(f"Constraints url: {constraints}")
            try:
                response = requests.head(constraints)
                if response.status_code != 200:
                    LOG.error(
                        f"Remote constraints file not accessible: {response.status_code}"
                    )
                    return False
                return True
            except Exception as e:
                LOG.error(f"Error accessing remote constraints: {e}")
                return False

        if not exists(constraints):
            LOG.error("Couldn't find the constraints file")
            return False
        return True

    # ------------------------------------------------------------------
    # Core pip operations
    # ------------------------------------------------------------------

    def pip_install(
        self,
        packages: List[str],
        constraints: Optional[str] = None,
        print_logs: bool = True,
    ) -> bool:
        """Install Python packages via pip or uv.

        Args:
            packages: Package specifiers to install.
            constraints: Optional constraints file path or URL.
            print_logs: Whether to print pip output to stdout.

        Returns:
            ``True`` if every package was installed successfully.
        """
        if not packages:
            LOG.error("no package list provided to install")
            self.play_error_sound()
            return False

        constraints = constraints or self.config.get(
            "constraints", self.DEFAULT_CONSTRAINTS
        )

        if not self.validate_constraints(constraints):
            self.play_error_sound()
            return False

        if self.UV is not None:
            pip_args = [self.UV, "pip", "install"]
        else:
            pip_args = [sys.executable, "-m", "pip", "install"]

        if constraints:
            pip_args += ["-c", constraints]
        if self.config.get("break_system_packages", False):
            pip_args += ["--break-system-packages"]
        if self.config.get("allow_alphas", False):
            pip_args += ["--pre"]

        with self.PIP_LOCK:
            for package in packages:
                LOG.info(f"[{self.service_name}] (pip) Installing {package}")
                pip_command = pip_args + [package]
                LOG.debug(" ".join(pip_command))
                proc = (
                    Popen(pip_command)
                    if print_logs
                    else Popen(pip_command, stdout=PIPE, stderr=PIPE)
                )
                if proc.wait() != 0:
                    stderr = proc.stderr
                    if stderr:
                        stderr = stderr.read().decode()
                    self.play_error_sound()
                    raise RuntimeError(stderr)

        self._on_install_complete()
        self.play_success_sound()
        return True

    def pip_uninstall(
        self,
        packages: List[str],
        constraints: Optional[str] = None,
        print_logs: bool = True,
    ) -> bool:
        """Uninstall Python packages via pip or uv.

        Protected packages listed in the constraints file cannot be removed.

        Args:
            packages: Package names to uninstall.
            constraints: Optional constraints file path or URL.
            print_logs: Whether to print pip output to stdout.

        Returns:
            ``True`` if every package was uninstalled successfully.
        """
        if not packages:
            LOG.error("no package list provided to uninstall")
            self.play_error_sound()
            return False

        constraints = constraints or self.config.get(
            "constraints", self.DEFAULT_CONSTRAINTS
        )

        if not self.validate_constraints(constraints):
            self.play_error_sound()
            return False

        # Resolve protected package list from constraints.
        if constraints.startswith("http"):
            cpkgs = requests.get(constraints).text.split("\n")
        elif exists(constraints):
            with open(constraints) as fh:
                cpkgs = fh.read().split("\n")
        else:
            cpkgs = [
                "ovos-core",
                "ovos-utils",
                "ovos-plugin-manager",
                "ovos-config",
                "ovos-bus-client",
                "ovos-workshop",
            ]

        cpkgs = [
            p.split("~")[0]
            .split("<")[0]
            .split(">")[0]
            .split("=")[0]
            .replace("_", "-")
            for p in cpkgs
        ]

        if any(p in cpkgs for p in packages):
            LOG.error(f"tried to uninstall a protected package: {packages}")
            self.play_error_sound()
            return False

        if self.UV is not None:
            pip_args = [self.UV, "pip", "uninstall", "-y"]
        else:
            pip_args = [sys.executable, "-m", "pip", "uninstall", "-y"]

        if self.config.get("break_system_packages", False):
            pip_args += ["--break-system-packages"]

        with self.PIP_LOCK:
            for package in packages:
                LOG.info(
                    f"[{self.service_name}] (pip) Uninstalling {package}"
                )
                pip_command = pip_args + [package]
                LOG.debug(" ".join(pip_command))
                proc = (
                    Popen(pip_command)
                    if print_logs
                    else Popen(pip_command, stdout=PIPE, stderr=PIPE)
                )
                if proc.wait() != 0:
                    stderr = proc.stderr.read().decode() if proc.stderr else ""
                    self.play_error_sound()
                    raise RuntimeError(stderr)

        self._on_uninstall_complete()
        self.play_success_sound()
        return True

    # ------------------------------------------------------------------
    # Extension hooks for subclasses
    # ------------------------------------------------------------------

    def _on_install_complete(self) -> None:
        """Called after a successful pip install.

        Override in subclasses to perform post-install actions such as
        reloading plugin entry-points (ovos-core does this via
        ``importlib.reload(ovos_plugin_manager)``).
        """

    def _on_uninstall_complete(self) -> None:
        """Called after a successful pip uninstall.

        Override in subclasses to perform post-uninstall actions.
        """

    # ------------------------------------------------------------------
    # Message bus handlers
    # ------------------------------------------------------------------

    def handle_install_python(self, message: Message) -> None:
        """Handle ``ovos.pip.install`` or ``ovos.pip.install.<service>``."""
        if not self.config.get("allow_pip"):
            LOG.error(InstallError.DISABLED.value)
            self.play_error_sound()
            self.bus.emit(
                message.reply(
                    "ovos.pip.install.failed",
                    {"error": InstallError.DISABLED.value},
                )
            )
            return

        pkgs = message.data.get("packages")
        if pkgs:
            try:
                success = self.pip_install(pkgs)
            except RuntimeError:
                success = False
            if success:
                self.bus.emit(message.reply("ovos.pip.install.complete"))
            else:
                self.bus.emit(
                    message.reply(
                        "ovos.pip.install.failed",
                        {"error": InstallError.PIP_ERROR.value},
                    )
                )
        else:
            self.bus.emit(
                message.reply(
                    "ovos.pip.install.failed",
                    {"error": InstallError.NO_PKGS.value},
                )
            )

    def handle_uninstall_python(self, message: Message) -> None:
        """Handle ``ovos.pip.uninstall`` or ``ovos.pip.uninstall.<service>``."""
        if not self.config.get("allow_pip"):
            LOG.error(InstallError.DISABLED.value)
            self.play_error_sound()
            self.bus.emit(
                message.reply(
                    "ovos.pip.uninstall.failed",
                    {"error": InstallError.DISABLED.value},
                )
            )
            return

        pkgs = message.data.get("packages")
        if pkgs:
            try:
                success = self.pip_uninstall(pkgs)
            except RuntimeError:
                success = False
            if success:
                self.bus.emit(message.reply("ovos.pip.uninstall.complete"))
            else:
                self.bus.emit(
                    message.reply(
                        "ovos.pip.uninstall.failed",
                        {"error": InstallError.PIP_ERROR.value},
                    )
                )
        else:
            self.bus.emit(
                message.reply(
                    "ovos.pip.uninstall.failed",
                    {"error": InstallError.NO_PKGS.value},
                )
            )
