import re
from datetime import date, datetime

from dateutil.parser import ParserError
from dateutil.parser import parse as dateparse
from servicelayer import env
from servicelayer.cache import make_key

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
    return dateparse(value, **parserkwargs).date()


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
            return ensure_date(value, dayfirst=True)
        except (TypeError, ParserError):
            return value


def re_first(pattern, string):
    try:
        return re.findall(pattern, string)[0]
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


def skip_while_testing(context, key=None, counter=-1):
    # try to speed up tests...
    if not env.to_bool("TESTING_MODE"):
        return False

    key = make_key(
        "skip_while_testing", context.crawler, context.stage, context.run_id, key
    )
    tag = context.get_tag(key)
    if tag is None:
        context.set_tag(key, 0)
        return False
    if tag > counter:
        context.log.debug("Skipping: %s" % key)
        return True
    context.set_tag(key, tag + 1)
