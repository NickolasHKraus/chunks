# Custom logic for converting a dictionary of unspecified type and depth into a
# JSON serializable dictionary.
#
# This logic is superceded by four lines of code leveraging json.JSONEncoder, a
# custom JSONEncoder for byte strings.
#
# See: https://docs.python.org/3/library/json.html#json.JSONEncoder

from typing import Any, Union

import json

import copy


def make_serializable_helper(x: Union[dict, list]) -> Union[dict, list]:
    """
    Given a list or dict, return its JSON serializable equivalent.
    """
    if len(x) == 0:
        return x
    if isinstance(x, list):
        l = []
        for i in x:
            if isinstance(i, bytes):
                l.append(i.decode())
            else:
                l.append(make_serializable_helper(i))
        return l
    for k, v in x.items():
        if isinstance(v, (list, dict)):
            x[k] = make_serializable_helper(v)
        elif isinstance(v, bytes):
            x[k] = v.decode()
    return x


def make_serializable(arg: Any) -> Any:
    """
    Given an argument, return its JSON serializable equivalent.
    """
    if isinstance(arg, str):
        return arg
    elif isinstance(arg, bytes):
        return arg.decode()
    elif isinstance(arg, dict):
        return make_serializable_helper(arg)
    else:
        return arg


def serialize(*args: Any) -> tuple:
    """
    Given a list of arguments, return their JSON serializable equivalents.
    """
    ret = []
    for arg in args:
        ret.append(make_serializable(arg))
    return tuple(ret)


def convert(data: dict) -> dict:
    """
    Convert a dictionary's keys and values from byte to character strings.

    NOTE:

    map(function, iterable, ...)

      Return an iterator that applies function to every item of iterable,
      yielding the results.
      ...

    See: https://docs.python.org/3/library/functions.html#map
    """
    if isinstance(data, bytes):
        return data.decode()
    if isinstance(data, dict):
        return dict(map(convert, data.items()))
    if isinstance(data, tuple):
        return tuple(map(convert, data))
    if isinstance(data, list):
        return list(map(convert, data))
    return data


class JSONEncoderBytes(json.JSONEncoder):
    """
    A custom JSONEncoder for byte strings.

    NOTE: To use a custom JSONEncoder subclass (e.g. one that overrides the
    default() method to serialize additional types), specify it with the cls
    kwarg; otherwise JSONEncoder is used.

    See: https://docs.python.org/3/library/json.html#json.JSONEncoder
    """
    def default(self, o):
        if isinstance(o, bytes):
            return o.decode()
        return json.JSONEncoder.default(self, o)


if __name__ == "__main__":
    d0 = {"a": "string"}
    d1 = {"a": b"byte"}
    d2 = {"a": {"a": b"byte"}}
    d3 = {"a": [{"a": b"byte"}]}
    d4a = {
        "a": "b",
        "byte": b"byte",
        "bytes": [b"byte", b"byte", b"byte"],
        "c": {
            "c1": None,
            "c2": None,
            "c3": None,
            "c4": None
        },
        "map": [{
            "a": "b",
            "byte": b"byte",
            "bytes": [b"byte", b"byte", b"byte"],
            "c": {
                "c1": None,
                "c2": None,
                "c3": None,
                "c4": None
            }}]
    }
    d4b = copy.copy(d4a)
    d4c = copy.copy(d4b)
    d0, d1, d2, d3, d4a = serialize(d0, d1, d2, d3, d4a)
    assert json.dumps(d4a) == json.dumps(d4b, cls=JSONEncoderBytes)
    print(convert(d4c))
