from banal import ensure_list, is_mapping
from furl import furl

from .incremental import skip_incremental
from .util import skip_while_testing


def _test(data, key, value):
    """
    test a dict recursively if key == value
    """
    for k, v in data.items():
        if k == key:
            yield v == value
        if isinstance(v, dict):
            yield from _test(v, key, value)
        if isinstance(v, list):
            for i in v:
                if is_mapping(i):
                    yield from _test(i, key, value)


def parse(context, data):
    res = context.http.rehash(data)

    for document in ensure_list(res.json["documents"]):
        filters = {
            "vorgangstyp": data["document_type"],
            "wahlperiode": data["legislative_term"],
        }
        if all(any(_test(document, k, v)) for k, v in filters.items()):
            if not skip_incremental(context, data):
                data["reference"] = document["dokumentnummer"]
                data["published_at"] = document["datum"]
                data["title"] = document["titel"]
                is_answer = document["drucksachetyp"] == "Antwort"
                data["is_answer"] = is_answer
                emitted_yet = False
                if not is_answer:
                    data["originators"] = [i["titel"] for i in document["urheber"]]
                else:
                    data["answerers"] = [i["titel"] for i in document["urheber"]]
                    # enrich with vorgangsdata to get originators
                    if document["vorgangsbezug_anzahl"] > 0:
                        process = [
                            i
                            for i in document["vorgangsbezug"]
                            if i["vorgangstyp"] == data["document_type"]
                        ][0]
                        fu = furl(data["url"])
                        apikey = fu.args["apikey"]
                        fu = furl(
                            "https://search.dip.bundestag.de/api/v1/vorgang/%s/"
                            % process["id"]
                        )
                        fu.args["apikey"] = apikey
                        context.emit(
                            "fetch_reference",
                            data={**data, **{"document": document, "url": fu.url}},
                        )
                        emitted_yet = True

                if not emitted_yet:
                    context.emit(
                        "download",
                        data={
                            **data,
                            **{
                                "url": document["fundstelle"]["pdf_url"],
                                "document": document,
                            },
                        },
                    )

                    if skip_while_testing(context, "yield_items", 10):
                        break

    # next page
    fu = furl(data["url"])
    if res.json["cursor"] != fu.args.get("cursor"):
        fu.args["cursor"] = res.json["cursor"]

        if not skip_while_testing(context, "paginate", 10):
            context.emit("cursor", data={**data, **{"url": fu.url}})


def parse_reference(context, data):
    """
    enrich with originators etc
    """
    res = context.http.rehash(data)
    data["reference_data"] = res.json
    data["originators"] = res.json["initiative"]
    context.emit(data={**data, **{"url": data["document"]["fundstelle"]["pdf_url"]}})
