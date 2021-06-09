from banal import ensure_list
from furl import furl

from .incremental import skip_incremental


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


def parse_detail(context, data):
    res = context.http.rehash(data)
    data["title"] = res.json["title"]
    f = furl(res.json["file_url"])
    data["url"] = f.join(data["url"], "/pdfs/", f.path.segments[-1]).url
    context.emit(data=data)
