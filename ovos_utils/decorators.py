from functools import lru_cache, wraps
from time import monotonic_ns
from typing import Callable, Optional, Any


class classproperty(property):
    """
    A decorator for creating a class-level property.

    Credit to Denis Rhyzhkov on Stackoverflow:
    https://stackoverflow.com/a/13624858/1280629

    Example:
        class MyClass:
            @classproperty
            def my_property(cls):
                return "Class-level property"
    """
    def __get__(self, owner_self: Optional[object], owner_cls: type) -> Any:
        return self.fget(owner_cls)


def timed_lru_cache(
        _func: Optional[Callable] = None, *,
        seconds: int = 7000, maxsize: int = 128, typed: bool = False
) -> Callable:
    """
    A version of lru_cache with an added timeout feature. After the specified timeout (in seconds),
    the cache is cleared and the function is recomputed.

    taken from: https://gist.github.com/Morreski/c1d08a3afa4040815eafd3891e16b945

    Args:
        _func (Optional[Callable]): The function to cache, used when the decorator is called directly.
        seconds (int): Timeout value in seconds. Default is 7000 seconds.
        maxsize (int): Maximum size of the cache. Default is 128.
        typed (bool): Whether to use different cache keys for different types of arguments. Default is False.

    Returns:
        Callable: A wrapped function that supports caching with a timeout.

    Example:
        @timed_lru_cache(seconds=3600)
        def expensive_computation(arg):
            # Some expensive computation here
            return result
    """
    def wrapper_cache(f: Callable) -> Callable:
        # Create a function wrapped with traditional lru_cache
        f = lru_cache(maxsize=maxsize, typed=typed)(f)
        # Convert seconds to nanoseconds for cache expiration time
        f.delta = seconds * 10 ** 9
        f.expiration = monotonic_ns() + f.delta

        @wraps(f)  # wraps is used to access the decorated function's attributes
        def wrapped_f(*args: Any, **kwargs: Any) -> Any:
            if monotonic_ns() >= f.expiration:
                # Clear the cache if expired and reset expiration time
                f.cache_clear()
                f.expiration = monotonic_ns() + f.delta
            return f(*args, **kwargs)

        wrapped_f.cache_info = f.cache_info
        wrapped_f.cache_clear = f.cache_clear
        return wrapped_f

    # To allow decorator to be used without arguments
    if _func is None:
        return wrapper_cache
    else:
        return wrapper_cache(_func)
