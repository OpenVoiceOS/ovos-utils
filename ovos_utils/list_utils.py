from typing import List, Union, Any


def rotate_list(l: List[Any], n: int = 1) -> List[Any]:
    """
    Rotate the elements of a list by a given number of positions.

    Args:
        l (List[Any]): The list to rotate.
        n (int): The number of positions to rotate the list. Default is 1.

    Returns:
        List[Any]: The rotated list.

    Example:
        rotate_list([1, 2, 3], 1) -> [2, 3, 1]
    """
    return l[n:] + l[:n]


def flatten_list(some_list: List[Union[List, tuple]], tuples: bool = True) -> List:
    """
    Flatten a list of lists or tuples into a single list.

    Args:
        some_list (List[Union[List, tuple]]): The list to flatten.
        tuples (bool): Whether to flatten both lists and tuples. Default is True.

    Returns:
        List: The flattened list.

    Example:
        flatten_list([[1, 2], [3, 4]]) -> [1, 2, 3, 4]
    """
    _flatten = lambda l: [item for sublist in l for item in sublist]
    if tuples:
        while any(isinstance(x, (list, tuple)) for x in some_list):
            some_list = _flatten(some_list)
    else:
        while any(isinstance(x, list) for x in some_list):
            some_list = _flatten(some_list)
    return some_list


def deduplicate_list(seq: List[str], keep_order: bool = True) -> List[str]:
    """
    Deduplicate a list while optionally maintaining the original order.

    Args:
        seq (List[str]): The list to deduplicate.
        keep_order (bool): Whether to preserve the order of elements. Default is True.

    Returns:
        List[str]: The deduplicated list.

    Notes:
        If `keep_order` is False, the function uses a set for faster deduplication.
    """
    if not keep_order:
        return list(set(seq))
    else:
        return list(dict.fromkeys(seq))
