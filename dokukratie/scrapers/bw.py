import re
from urllib.parse import urljoin

from furl import furl

from .incremental import skip_incremental


def _parse(body, base_url):
    data = {}
    for el in body:
        if el.tag == "hr" and data:
            yield data
        if el.tag == "a":
            data["url"] = urljoin(base_url, el.get("href"))
            data["title"] = el.text
        if el.tag == "ul":
            data["reference"], date = [i.text for i in el][:2]
            data["published_at"] = re.findall(r"\d{2}\.\d{2}\.\d{4}", date)[0]
            data["originators"] = "".join([i for i in el][-1].itertext())


def parse(context, data):
    # we already have detail data, forward to clean stage
    if "reference" in data:
        context.emit(rule="clean", data=data)
        return

    res = context.http.rehash(data)

    # we reached the end of the listing
    if "keine weiteren ergebnisse" in res.text.lower():
        return

    # parse listing, yield detail entries
    for detail_data in _parse(res.html.body, res.url):
        if not skip_incremental(context, detail_data):
            context.emit(rule="fetch", data={**data, **detail_data})

    # increment listing
    fu = furl(res.url)
    offset = int(fu.args.get("offset", 0))
    fu.args["offset"] = offset + int(fu.args.get("limit", 10))
    context.emit(rule="fetch", data={**data, **{"url": fu.url}})