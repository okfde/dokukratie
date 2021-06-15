import re
from datetime import date, datetime

from dateutil.parser import ParserError
from dateutil.parser import parse as dateparse
from servicelayer import env

from .exceptions import RegexError


def get_env_or_context(context, key, default=None):
    return env.get(key) or context.params.get(key.lower(), default)


def ensure_date(value, **parserkwargs):
    if value is None:
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    value = str(value)
    try:
        do_raise = parserkwargs.pop("raise_on_error", False)
        return dateparse(value, **parserkwargs).date()
    except ParserError as e:
        if do_raise:
            raise e
        return None


def cast(value):
    if not isinstance(value, (str, float, int)):
        return value
    if isinstance(value, str):
        value = value.strip()
    try:
        if float(value) == int(value):
            return int(value)
        return float(value)
    except (TypeError, ValueError):
        try:
            return ensure_date(value, dayfirst=True, raise_on_error=True)
        except (TypeError, ParserError):
            return value


def re_first(pattern, string):
    try:
        value = re.findall(pattern, string)[0]
        return value.strip()
    except Exception as e:
        raise RegexError(str(e), string)


def get_value_from_xp(html, path):
    part = html.xpath(path)
    if isinstance(part, list) and part:
        part = part[0]
    if hasattr(part, "text"):
        part = part.text
    if isinstance(part, str):
        return part.strip()
    return part


def flatten_dict(d):
    def items():
        for key, value in d.items():
            if isinstance(value, dict):
                for subkey, subvalue in flatten_dict(value).items():
                    yield key + "." + subkey, subvalue
            else:
                yield key, value

    return dict(items())
