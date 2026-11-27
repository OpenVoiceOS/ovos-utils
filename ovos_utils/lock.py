"""Thread and process locks on ``filelock``.

Drop-in for ``combo_lock.ComboLock`` and ``combo_lock.NamedLock``.
``NamedLock`` uses the same lock file path as ``combo_lock``, so a process
on this module and a process on ``combo_lock`` exclude each other.
"""
import platform
import tempfile
from base64 import b64encode
from pathlib import Path
from threading import Lock

from filelock import FileLock, Timeout

LOCK_FILE_ACCESS_RIGHTS = 0o666


def _make_global_dir(path: Path):
    try:
        path.mkdir(parents=True)
    except FileExistsError:
        if not path.is_dir():
            raise
    else:
        path.chmod(0o777)


def _lock_dir() -> Path:
    if platform.system() == "Linux":
        from memory_tempfile import MemoryTempfile
        base = MemoryTempfile(fallback=True).gettempdir()
    else:
        base = tempfile.gettempdir()
    path = Path(base, "combo_locks")
    try:
        _make_global_dir(path)
    except OSError:
        path = Path(tempfile.gettempdir(), "combo_locks")
        _make_global_dir(path)
    return path


class ComboLock:
    """A lock held by one thread of one process at a time."""

    def __init__(self, path):
        self.path = Path(path)
        self._init_plock_file()
        self.plock = FileLock(str(self.path), mode=LOCK_FILE_ACCESS_RIGHTS)
        self.tlock = Lock()

    def _init_plock_file(self):
        if not self.path.exists():
            self.path.touch()
            self.path.chmod(LOCK_FILE_ACCESS_RIGHTS)

    def acquire(self, blocking: bool = True) -> bool:
        try:
            return self._acquire(blocking)
        except FileNotFoundError:
            self._init_plock_file()
            return self._acquire(blocking)

    def _acquire(self, blocking: bool) -> bool:
        if blocking:
            self.tlock.acquire()
            self.plock.acquire()
            return True
        if not self.tlock.acquire(blocking=False):
            return False
        try:
            self.plock.acquire(timeout=0.01)
        except Timeout:
            self.tlock.release()
            return False
        return True

    def release(self):
        self.plock.release()
        self.tlock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, _type, value, traceback):
        self.release()


class NamedLock(ComboLock):
    """A ``ComboLock`` found by name in a shared RAM directory."""

    def __init__(self, name: str):
        filename = b64encode(name.encode(), altchars=b"-_").decode() + ".lock"
        super().__init__(_lock_dir() / filename)
        self.name = name
