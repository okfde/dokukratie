import json
import re
from datetime import date, datetime
from urllib.parse import urljoin

from banal import ensure_dict, ensure_list
from dateparser import parse as dateparse2  # FIXME
from dateutil.parser import ParserError
from dateutil.parser import parse as dateparse
from jinja2 import BaseLoader, Environment
from memorious.operations.parse import URL_TAGS, collapse_spaces, make_key
from mmmeta.util import datetime_to_json
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
    except Exception:
        # FIXME
        try:
            return dateparse2(value, **parserkwargs).date()
        except Exception as e:
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


def re_group(pattern, string, group):
    try:
        m = re.match(pattern, string)
        return m.group(group)
    except Exception:
        try:
            return re_first(pattern, string)
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


def pretty_dict(d):
    """
    for logging purposes
    """
    return json.dumps(
        {k: v for k, v in d.items() if v}, indent=2, default=datetime_to_json
    )


def get_form(context, html, xp):
    """
    return action, data
    """
    form = html.find(xp)
    if form is None:
        context.log.error(f"Cannot find form: `{xp}`")
        context.crawler.cancel()
        return None, None
    return get_value_from_xp(form, "@action"), {
        **{i.name: i.value for i in form.findall(".//input")},
        **{i.name: i.value for i in form.findall(".//select")},
    }


def generate_url(template, data):
    tmpl = Environment(loader=BaseLoader).from_string(template)
    return tmpl.render(**data)


def extract(context, data):
    if "extract" in context.params:  # new implementation
        patterns = ensure_list(context.params["extract"]["patterns"])
        source_key = context.params["extract"]["source"]
        source = data.get(source_key)
        if source is None:
            context.log.warning("No source data found")
            return
        if source_key != "metadata":  # FIXME migration
            data["metadata"] = data[source_key]
        for pattern in patterns:
            pattern = re.compile(pattern)  # yaml escaping & stuff
            m = re.match(pattern, source)
            if m is not None:
                data.update(m.groupdict())
                break

    else:
        for key, patterns in ensure_dict(context.params.get("extractors")).items():
            if key not in data:
                continue
            if isinstance(data[key], list):  # FIXME migration
                if len(data[key]) == 1:
                    data[key] = data[key][0]
            if isinstance(data[key], datetime):
                continue

            # save original for further re-extracting
            if f"{key}__unextracted" not in data:
                data[f"{key}__unextracted"] = data[key]

            value = None
            patterns = ensure_list(patterns)
            for pattern in patterns:
                pattern = re.compile(pattern)
                try:
                    value = re_group(pattern, data[f"{key}__unextracted"], key)
                    if value is not None:
                        data[key] = value
                        break
                except RegexError:
                    pass
            # still nothing found:
            if value is None:
                context.log.warning(
                    "Can't extract metadata for `%s`: [%s] %s"
                    % (key, pattern.pattern, data[f"{key}__unextracted"])
                )
                data[key] = None


def parse_html_item(context, data, html):
    # FIXME adjust memorious `parse_html` ?
    context.log.info("Parse item")

    include = context.params.get("include_paths")
    if include is None:
        roots = [html]
    else:
        roots = []
        for path in include:
            roots = roots + html.xpath(path)

    seen = set()
    for root in roots:
        for tag_query, attr_name in URL_TAGS:
            for element in root.xpath(tag_query):
                attr = element.get(attr_name)
                if attr is None:
                    continue

                try:
                    url = urljoin(data["url"], attr)
                    key = url
                except Exception:
                    context.log.warning("Invalid URL: %r", attr)
                    continue

                if url is None or key is None or key in seen:
                    continue
                seen.add(key)

                tag = make_key(context.run_id, key)
                if context.check_tag(tag):
                    continue
                context.set_tag(tag, None)
                data["url"] = url

                if data.get("title") is None:
                    # Option to set the document title from the link text.
                    if context.get("link_title", False):
                        data["title"] = collapse_spaces(element.text_content())
                    elif element.get("title"):
                        data["title"] = collapse_spaces(element.get("title"))

                context.http.session.headers["Referer"] = url
                context.emit(rule="fetch", data=data)
