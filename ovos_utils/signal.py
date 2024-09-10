import os
import os.path
import tempfile
import time

from ovos_utils.log import LOG, log_deprecation, deprecated


@deprecated("ovos_utils.signal module has been deprecated!", "0.2.0")
def get_ipc_directory(domain=None, config=None):
    """Get the directory used for Inter Process Communication

    Files in this folder can be accessed by different processes on the
    machine.  Useful for communication.  This is often a small RAM disk.

    Args:
        domain (str): The IPC domain.  Basically a subdirectory to prevent
            overlapping signal filenames.
        config (dict): mycroft.conf, to read ipc directory from

    Returns:
        str: a path to the IPC directory
    """
    if config is None:
        log_deprecation(f"Expected a dict config and got None.", "0.1.0")
        try:
            from ovos_config.config import Configuration
            config = Configuration()
        except ImportError:
            LOG.warning("Config not provided and ovos_config not available")
            config = dict()
    path = config.get("ipc_path")
    if not path:
        # If not defined, use /tmp/mycroft/ipc
        path = os.path.join(tempfile.gettempdir(), "mycroft", "ipc")
    return ensure_directory_exists(path, domain)


@deprecated("use 'from ovos_utils.file_utils import ensure_directory_exists' instead", "0.2.0")
def ensure_directory_exists(directory, domain=None):
    """ Create a directory and give access rights to all

    Args:
        domain (str): The IPC domain.  Basically a subdirectory to prevent
            overlapping signal filenames.

    Returns:
        str: a path to the directory
    """
    from ovos_utils.file_utils import ensure_directory_exists as _ede
    return _ede(directory, domain)


@deprecated("ovos_utils.signal module has been deprecated!", "0.2.0")
def create_file(filename):
    """ Create the file filename and create any directories needed

        Args:
            filename: Path to the file to be created
    """
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass
    with open(filename, 'w') as f:
        f.write('')


@deprecated("ovos_utils.signal module has been deprecated!", "0.2.0")
def create_signal(signal_name, config=None):
    """Create a named signal

    Args:
        signal_name (str): The signal's name.  Must only contain characters
            valid in filenames.
        config (dict): mycroft.conf, to read ipc directory from
    """
    try:
        path = os.path.join(get_ipc_directory(config=config),
                            "signal", signal_name)
        create_file(path)
        return os.path.isfile(path)
    except IOError:
        return False


@deprecated("ovos_utils.signal module has been deprecated!", "0.2.0")
def check_for_signal(signal_name, sec_lifetime=0, config=None):
    """See if a named signal exists

    Args:
        signal_name (str): The signal's name.  Must only contain characters
            valid in filenames.
        sec_lifetime (int, optional): How many seconds the signal should
            remain valid.  If 0 or not specified, it is a single-use signal.
            If -1, it never expires.
        config (dict): mycroft.conf, to read ipc directory from

    Returns:
        bool: True if the signal is defined, False otherwise
    """
    path = os.path.join(get_ipc_directory(config=config),
                        "signal", signal_name)
    if os.path.isfile(path):
        if sec_lifetime == 0:
            # consume this single-use signal
            os.remove(path)
        elif sec_lifetime == -1:
            return True
        elif int(os.path.getctime(path) + sec_lifetime) < int(time.time()):
            # remove once expired
            os.remove(path)
            return False
        return True

    # No such signal exists
    return False
