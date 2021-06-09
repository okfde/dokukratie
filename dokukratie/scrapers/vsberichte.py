from banal import ensure_list
from furl import furl

from .incremental import skip_incremental
from .util import skip_while_testing


def parse_list(context, data):
    res = context.http.rehash(data)
    f = furl(data["url"])
    for jurisdiction in ensure_list(res.json["reports"]):
        publisher = {
            "id": jurisdiction["jurisdiction_escaped"],
            "name": jurisdiction["jurisdiction"],
        }
        for year in ensure_list(jurisdiction["years"]):
            detail_data = {
                "publisher": publisher,
                "published_at": f"{year}-12-31",  # FIXME
                "url": (f / jurisdiction["jurisdiction_escaped"] / str(year)).url,
            }
            if not skip_incremental(context, detail_data):
                context.emit(data={**data, **detail_data})
