"""JavaScript value semantics that the Node code relies on, reproduced for the port."""

import math
import re
from typing import Any

_JS_WHITESPACE = (
    "\t\n\x0b\x0c\r \xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
)
_MAX_SAFE_INTEGER = 2**53


def _to_js_number(n: int) -> int | float:
    if abs(n) <= _MAX_SAFE_INTEGER:
        return n
    try:
        return float(n)
    except OverflowError:
        return math.inf if n > 0 else -math.inf


def _parse_int_str(s: str) -> int | float:
    s = s.lstrip(_JS_WHITESPACE)
    sign = -1 if s[:1] == "-" else 1
    if s[:1] in ("+", "-"):
        s = s[1:]
    if s[:2] in ("0x", "0X"):
        match, radix = re.match(r"[0-9a-fA-F]+", s[2:]), 16
    else:
        match, radix = re.match(r"[0-9]+", s), 10
    if not match:
        return math.nan
    try:
        n = int(match.group(), radix)
    except ValueError:
        return sign * math.inf
    return _to_js_number(sign * n)


def parse_int(value: Any) -> int | float:
    """JS ``parseInt(value)`` without a radix; ``float("nan")`` stands in for NaN.

    Strings and numbers follow JS exactly. Every other type returns NaN, which
    differs from JS only for arrays (``parseInt([5])`` is 5 in JS).
    """
    if isinstance(value, str):
        return _parse_int_str(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return math.nan
    if isinstance(value, int) and abs(value) <= _MAX_SAFE_INTEGER:
        return value
    try:
        x = float(value)
    except OverflowError:
        return math.nan
    if math.isnan(x) or math.isinf(x):
        return math.nan
    if x == 0:
        return 0
    if 1e-6 <= abs(x) < 1e21:
        return _to_js_number(math.trunc(x))
    digit = int(repr(abs(x))[0])
    return digit if x > 0 else -digit


def strict_equals(a: Any, b: Any) -> bool:
    """JS ``a === b`` for values decoded from JSON or BSON.

    Objects and arrays compare by identity in JS, so two separately decoded
    containers are never equal. ``None`` stands for both null and undefined.
    """
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    return a is None and b is None


def truthy(value: Any) -> bool:
    """JS truthiness: only null/undefined, false, 0, NaN and "" are falsy."""
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return not (value == 0 or value != value)
    if isinstance(value, str):
        return value != ""
    return True
