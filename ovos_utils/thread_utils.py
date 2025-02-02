import signal
from functools import wraps
from threading import Thread, Event
from typing import Callable, Optional, Any

import kthread

from ovos_utils.log import LOG


def threaded_timeout(timeout: int = 5) -> Callable:
    """
    Decorator to run a function in a separate thread with a specified timeout.
    If the timeout is exceeded, an exception is raised and the thread is terminated.

    Args:
        timeout (int): Timeout in seconds to wait before terminating the process. Default is 5.

    Returns:
        Callable: A decorated function that will run in a separate thread with a timeout.

    Example:
        @threaded_timeout(timeout=10)
        def long_running_task():
            pass
    """

    def deco(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            res = [Exception(f'function [{func.__name__}] timeout '
                             f'[{timeout}] exceeded!')]

            def func_wrapped():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e

            t = Thread(target=func_wrapped)
            t.daemon = True
            try:
                t.start()
                t.join(timeout)
            except Exception as je:
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret

        return wrapper

    return deco


def create_killable_daemon(target: Callable, args: tuple = (), kwargs: Optional[dict] = None,
                           autostart: bool = True) -> kthread.KThread:
    """
    Helper to create and start a killable daemon thread.

    Args:
        target (Callable): The target function for the thread.
        args (tuple): Arguments to pass to the target function. Default is an empty tuple.
        kwargs (Optional[dict]): Keyword arguments to pass to the target function. Default is None.
        autostart (bool): Whether to start the thread immediately after creation. Default is True.

    Returns:
        kthread.KThread: The created thread.

    Example:
        create_killable_daemon(target=my_function, args=(arg1, arg2))
    """
    t = kthread.KThread(target=target, args=args, kwargs=kwargs)
    t.daemon = True
    if autostart:
        t.start()
    return t


def create_daemon(target: Callable, args: tuple = (), kwargs: Optional[dict] = None, autostart: bool = True) -> Thread:
    """
    Helper to create and start a standard daemon thread.

    Args:
        target (Callable): The target function for the thread.
        args (tuple): Arguments to pass to the target function. Default is an empty tuple.
        kwargs (Optional[dict]): Keyword arguments to pass to the target function. Default is None.
        autostart (bool): Whether to start the thread immediately after creation. Default is True.

    Returns:
        Thread: The created thread.

    Example:
        create_daemon(target=my_function, args=(arg1, arg2))
    """
    t = Thread(target=target, args=args, kwargs=kwargs)
    t.daemon = True
    if autostart:
        t.start()
    return t


def wait_for_exit_signal() -> None:
    """
    Blocks until a KeyboardInterrupt is received. This function will allow the program to
    exit gracefully when interrupted by the user.

    Returns:
        None

    Example:
        wait_for_exit_signal()  # The program will block here until KeyboardInterrupt is received.
    """
    exit_event = Event()

    def signal_handler(signum, frame):
        LOG.debug("Exiting on signal %s", signal.Signals(signum).name)
        exit_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        exit_event.wait()
    except KeyboardInterrupt:
        LOG.debug("Exiting on KeyboardInterrupt")
