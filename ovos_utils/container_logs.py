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
"""Bridges Docker/Podman container stdout into the small, familiar set of
per-category log files a file-based install already produces (skills.log,
audio.log, voice.log, bus.log, phal.log, gui.log, plus other.log for
anything uncategorized), so ``ovos-logs`` and every other consumer of
:func:`ovos_utils.log.get_available_logs` can read a Docker/Podman install
the same way it reads a systemd/venv one.

On a Docker/Podman install following ``ovos-docker``'s own documented example
config (``"logs": {"path": "stdout"}``), there are no log files on the host
at all - only container stdout - so tooling built around log files has
nothing to work with there. This module makes container stdout look like an
ordinary log directory instead of teaching every consumer a second, parallel
way to receive log lines.

Ported from a working, tested reference implementation contributed by
andlo (https://github.com/andlo/ovos-tui-client/blob/main/ovos_tui_client/services.py),
confirmed there against a real, running ovos-docker install (26 containers).
"""
import subprocess
from pathlib import Path
from typing import List, Optional


def find_container_binary() -> Optional[str]:
    """Returns "docker" or "podman", whichever actually works, or None."""
    for binary in ("docker", "podman"):
        try:
            result = subprocess.run([binary, "ps"], capture_output=True,
                                    timeout=5)
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            continue
        if result.returncode == 0:
            return binary
    return None


def list_container_names(binary: Optional[str] = None) -> List[str]:
    """Returns a sorted list of container names that look OVOS-related
    (containing "ovos" or "hivemind", case-insensitive, matching
    ovos-docker's own naming convention), or [] if no runtime is available
    or none match.

    @param binary: "docker" or "podman"; auto-detected if not given
    """
    binary = binary or find_container_binary()
    if binary is None:
        return []
    try:
        result = subprocess.run([binary, "ps", "--format", "{{.Names}}"],
                                capture_output=True, text=True, timeout=5)
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return []
    if result.returncode != 0:
        return []
    names = [n.strip() for n in result.stdout.splitlines() if n.strip()]
    matching = [n for n in names if "ovos" in n.lower() or "hivemind" in n.lower()]
    return sorted(matching)


def categorize_container_name(name: str) -> str:
    """Maps a Docker/Podman container name to the same category names a
    file-based install already uses - "skills", "audio", "voice", "bus",
    "phal", "gui" - or "other" if it doesn't recognizably fit one of those.

    Pattern-matched, not an exhaustive lookup table: "ovos_skill_" (any
    suffix) always maps to "skills", matching how every individual skill
    already shares one skills.log file on a normal install, not one file
    per skill. "ovos_core" also maps to "skills" specifically because its
    own log content (intent-service/pipeline handling) is exactly what
    already lands in skills.log on a normal install.

    @param name: container name, e.g. "ovos_skill_alarm" or "ovos_audio"
    @return: one of "skills", "audio", "voice", "bus", "phal", "gui", "other"
    """
    n = name.lower()
    if n.startswith("ovos_skill") or n == "ovos_core":
        return "skills"
    if n == "ovos_audio":
        return "audio"
    if n == "ovos_listener":
        return "voice"
    if n == "ovos_messagebus":
        return "bus"
    if n.startswith("ovos_phal"):
        return "phal"
    if "gui" in n:
        return "gui"
    return "other"


def start_container_log_bridges(container_names: List[str],
                                 target_dir: Path) -> List[subprocess.Popen]:
    """Bridges Docker/Podman container stdout into the same small set of
    per-category log files a file-based install already produces, under
    ``target_dir`` - not one file per container. That directory can then be
    passed as-is to any ``ovos-logs`` command's ``--paths``/``-p`` option (or
    to :func:`ovos_utils.log.get_available_logs`), reusing 100% of the
    existing file-tailing/coloring/filtering machinery.

    Multiple containers sharing a category (most commonly "skills" - every
    ``ovos_skill_*`` container) each get their own ``docker logs -f``
    subprocess, but all of them append to the same shared file - concurrent
    appends from separate processes are safe here without explicit locking,
    since POSIX guarantees a single write() to a file opened with O_APPEND is
    atomic as long as it is smaller than PIPE_BUF (4096 bytes on Linux),
    which holds for any normal single log line.

    Returns a list of ``subprocess.Popen`` handles - the caller owns their
    lifecycle and MUST terminate them (see :func:`stop_container_log_bridges`);
    they are not cleaned up automatically here. Returns ``[]`` immediately
    (no processes started) if neither docker nor podman is available.

    @param container_names: container names to bridge, e.g. from
        :func:`list_container_names`
    @param target_dir: directory the per-category ``.log`` files are
        appended to; created if missing
    """
    binary = find_container_binary()
    if binary is None:
        return []
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    handles = []
    for name in container_names:
        category = categorize_container_name(name)
        log_path = target_dir / f"{category}.log"
        log_file = open(log_path, "a")
        try:
            proc = subprocess.Popen(
                [binary, "logs", "-f", "--tail", "0", name],
                stdout=log_file, stderr=subprocess.STDOUT,
            )
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            log_file.close()
            continue
        handles.append(proc)
    return handles


def stop_container_log_bridges(handles: List[subprocess.Popen]) -> None:
    """Terminates every subprocess started by
    :func:`start_container_log_bridges`. Gives each a moment to exit
    cleanly before force-killing, and never raises even if a process
    already exited on its own (e.g. the container itself stopped).

    @param handles: the list returned by :func:`start_container_log_bridges`
    """
    for proc in handles:
        if proc.poll() is not None:
            continue  # already exited
        try:
            proc.terminate()
        except OSError:
            continue  # process died between poll() and terminate()
    for proc in handles:
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        except OSError:
            continue  # process already gone
