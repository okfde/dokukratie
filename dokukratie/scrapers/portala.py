import json

from .util import pretty_dict


def search(context, data):
    """
    do a post request to the search overview page for given
    legislative_term and document_type to get report_id
    """
    with open(context.params["query_template"]) as f:
        query = f.read()

    query = query % data
    query = json.loads(query)
    context.log.debug(pretty_dict(query))

    res = context.http.post(context.params["url"], json=query)

    context.log.info("Search [%s]: %s" % (res.status_code, res.url))
    context.emit(data={**data, **res.serialize()})


def fetch_results(context, data):
    item_count = int(data["item_count"])
    start = data.get("start", 0)
    chunksize = context.params.get("chunksize", 50)
    report_id = data["report_id"]
    url = context.params["url"]
    res = context.http.get(
        url, params={"report_id": report_id, "start": start, "chunksize": chunksize}
    )
    context.emit(data={**data, **res.serialize()})
    if start + chunksize < item_count:
        context.log.info(f"Paginate: {start + chunksize}")
        context.recurse(data={**data, **{"start": start + chunksize}})
