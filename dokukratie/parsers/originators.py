import re

from banal import ensure_list


PATTERNS = (
    (("name", "party"), re.compile(r"(?P<name>[\w\s]+)\s\((?P<party>[\w\s\.-]+)\)")),
)


def parse(value):
    value = ensure_list(value)

    def _parse():
        for item in value:
            if item is not None:
                for i in item.split(","):
                    i = i.strip()
                    for keys, pat in PATTERNS:
                        m = re.match(pat, i)
                        if m:
                            yield {k: m.group(k) for k in keys}

    return [i for i in _parse()] or []
