from datetime import datetime
from itertools import product

import jq
from banal import clean_dict, ensure_dict, ensure_list
from furl import furl
from memorious.helpers.rule import Rule
from memorious.operations.fetch import fetch as memorious_fetch
from memorious.operations.parse import parse_for_metadata, parse_html
from memorious.operations.store import directory as memorious_store
from mmmeta.util import casted_dict

from ..parsers import parse as parse_metadata
from .exceptions import MetaDataError, RegexError
from .incremental import skip_incremental
from .mmmeta import get_start_date
from .util import ensure_date, extract, flatten_dict, generate_url
from .util import get_env_or_context as _geoc
from .util import get_form, parse_html_item, pretty_dict, re_first


def init(context, data=None):
    """
    initializer for all crawlers even if they don't use the scraper class

    we want to have a consistent way to initialize scrapers (optionally via env
    vars) with required data:
    - document_type
    and optional data:
    - legislative_term
    - start_date (for `published_at`)
    - end_date (for `published_at`)
    """
    legislative_terms = ensure_list(_geoc(context, "LEGISLATIVE_TERMS")) or [None]
    document_types = ensure_list(_geoc(context, "DOCUMENT_TYPES")) or [None]
    dateformat = context.params.get("dateformat", "%Y-%m-%d")
    start_date = ensure_date(_geoc(context, "START_DATE"))
    end_date = ensure_date(_geoc(context, "END_DATE"))

    # get from mmmeta
    if start_date is None:
        start_date = ensure_date(get_start_date(context))

    if start_date is not None:
        start_date = start_date.strftime(dateformat)
        if end_date is None:
            end_date = datetime.now().date()
    if end_date is not None:
        end_date = end_date.strftime(dateformat)

    for legislative_term, document_type in product(legislative_terms, document_types):
        if document_type:
            document_type = context.crawler.config["document_types"][document_type]
        data = clean_dict(
            {
                "legislative_term": legislative_term,
                "document_type": document_type,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        context.log.debug(f"Using parameters: {pretty_dict(data)}")
        url_template = context.params.get("url_template")
        if url_template is not None:
            url = generate_url(url_template, data)
        else:
            url = context.params.get("url")
        if url is not None:
            fu = furl(url)
            for key, value in ensure_dict(context.params.get("urlparams")).items():
                fu.args[key] = value
            for key, param in ensure_dict(context.params.get("param_names")).items():
                if key in data:
                    fu.args[param] = data[key]
            data["url"] = fu.url

        context.emit(data=data)


def parse(context, data):
    """
    an extended parse to handle incremental scraping
    and to parse listings (config: items)
    """

    should_emit = context.params.get("emit") is True
    should_parse_html = context.params.get("parse_html", True) is True

    if not skip_incremental(context, data):
        with context.http.rehash(data) as result:
            if result.html is not None:
                # items listing scraping
                if "items" in context.params:
                    for item in result.html.xpath(context.params["items"]):
                        item_data = {k: v for k, v in data.items()}
                        parse_for_metadata(context, item_data, item)
                        extract(context, item_data)
                        if not skip_incremental(context, item_data):
                            if should_parse_html:
                                parse_html_item(context, item_data, item)
                            if should_emit:
                                context.emit(data=item_data)
                else:
                    # Get extra metadata from the DOM
                    parse_for_metadata(context, data, result.html)
                    extract(context, data)
                    # maybe data is updated with unique identifier for incremental skip
                    if not skip_incremental(context, data) and should_parse_html:
                        parse_html(context, data, result)

            rules = context.params.get("store") or {"match_all": {}}
            if Rule.get_rule(rules).apply(result):
                context.emit(rule="store", data=data)
            if should_emit:
                context.emit(data=data)


def fetch(context, data):
    """
    an extended fetch to be able to skip_incremental based on passed data dict
    and reduce fetches while testing
    """
    for key, value in ensure_dict(context.params.get("headers")).items():
        context.http.session.headers[key] = value
    context.log.debug(f"Headers: {pretty_dict(context.http.session.headers)}")
    context.log.debug(f"Cookies: {pretty_dict(context.http.session.cookies)}")

    url = context.params.get("url") or data.get("url")

    if "rewrite" in context.params:
        method = context.params["rewrite"]["method"]
        method_data = context.params["rewrite"]["data"]
        if method == "replace":
            url = url.replace(*method_data)
        if method == "template":
            url = generate_url(method_data, data)

    if url is None:
        context.log.error("No url specified.")
        return
    else:
        data["url"] = url

    f = furl(data["url"])
    if f.scheme is None:
        base_url = context.crawler.config["scraper"]["url"]
        data["url"] = furl(base_url).join(f).url

    if not skip_incremental(context, data):
        memorious_fetch(context, data)


DELETE_KEYS = ("page", "formdata")

# don't apply typing here:
UNCASTED_KEYS = ("modified_at", "retrieved_at", "reference")

DATE_KEYS = ("published_at",)


def clean(context, data, emit=True):
    """
    clean metadata and make sure it is as it is supposed to be

    optional parameters in yaml config:
        extractors: key, value dict for fields to extract their content via regex
    """

    if context is not None:
        # add some crawler metadata
        for key in ("publisher", "scraper"):
            if key in context.crawler.config:
                data[key] = context.crawler.config[key]

        # document type to universal key
        if "document_type" in data:
            doctype_keys = {
                v: k for k, v in context.crawler.config["document_types"].items()
            }
            data["document_type"] = doctype_keys.get(
                data["document_type"], data["document_type"]
            )

        # extract some extra data
        extract(context, data)

        # rewrite some values
        for key, values in ensure_dict(context.params.get("values")).items():
            if data.get(key) in values:
                data[key] = values[data[key]]

        # more parsing
        for key, parser in ensure_dict(context.params.get("parse")).items():
            if key in data:
                pat = re.compile(parser["pattern"])
                data[key] = [
                    re.match(pat, value).groupdict()
                    for value in data[key].split(parser.get("split"))
                ]

    # ensure document id metadata
    if "reference" in data:
        try:
            data["reference"] = re_first(r"\d{1,2}\/\d+", data["reference"])
        except RegexError:
            context.emit_warning(
                MetaDataError(f"Can not extract reference from `{data['reference']}`")
            )
            return
        data["legislative_term"], data["document_id"] = data["reference"].split("/")
    elif "document_id" in data and "legislative_term" in data:
        data["reference"] = "{legislative_term}/{document_id}".format(**data)
    else:
        context.emit_warning(
            MetaDataError(
                "Either `reference` or `legislative_term` and `document_id` must be present in metadata"  # noqa
            )
        )
        return

    # unique foreign id accross all scrapers:
    data["foreign_id"] = "%s-%s" % (
        data["publisher"]["jurisdiction"]["id"],
        data["reference"],
    )

    # cleanup and type
    for key in DELETE_KEYS:
        if key in data:
            del data[key]
    parserkwargs = ensure_dict(context.params.get("dateparser"))
    for key in DATE_KEYS:
        if key in data:
            data[key] = ensure_date(data[key], **parserkwargs)
    data = casted_dict(data, ignore_keys=UNCASTED_KEYS)

    # emit to next stage or return
    if context is not None and emit:
        context.emit(data=data)
    else:
        return data


def store(context, data):
    """
    an extended store to be able to set skip_incremental
    """
    memorious_store(context, data)
    incremental = ensure_dict(data.get("skip_incremental"))
    if incremental.get("target") == context.stage.name:
        if incremental.get("key") is not None:
            context.set_tag(incremental["key"], True)
    # during testing mode:
    skip_incremental(context, data)


def parse_json(context, data):
    """
    parse a json response and emit data dict based on config:

    extract: new key, source key (dot notation) for extracting data
    yield: if set, iterate through this key and emit for every item

    new implementation: use `jq`!
    """
    res = context.http.rehash(data)
    jsondata = clean_dict(flatten_dict(res.json))

    if "jq" in context.params:
        pattern = context.params["jq"]
        res = jq.compile(pattern).input(jsondata)
        for item in res.all():
            context.emit(data={**data, **item})
        return

    def _extract(jsondata=jsondata, data=data):
        for key, path in ensure_dict(context.params.get("extract")).items():
            try:
                data[key] = jsondata[path]
            except KeyError:
                context.emit_warning(
                    f"Can not extract `{path}` from {pretty_dict(jsondata)}"
                )
        return data

    if "yield" in context.params:
        for item in ensure_list(jsondata.get(context.params["yield"])):
            context.emit(data={**data, **_extract(item)})
        return

    context.emit(data=_extract())


def post(context, data):
    """
    do a post request with json data
    """
    url = data.get("url", context.params.get("url"))

    for key, value in ensure_dict(context.params.get("headers")).items():
        context.http.session.headers[key] = value
    context.log.debug(f"Headers: {pretty_dict(context.http.session.headers)}")

    if url:
        json_data = clean_dict(ensure_dict(context.params.get("json")))

        # direct json post request
        if json_data:
            context.log.debug(f"Post data: {pretty_dict(json_data)}")
            context.log.debug(f"Post url: {url}")
            res = context.http.post(url, json=json_data)
            context.emit(data={**data, **res.serialize()})
            return

        # handle form if any
        post_data = clean_dict(ensure_dict(context.params.get("data")))
        form = context.params.get("form")

        if form:
            res = context.http.rehash(data)
            action, formdata = get_form(context, res.html, form)
            url = furl(url).join(action).url
            post_data = {**formdata, **post_data}

        context.log.debug(f"Post data: {pretty_dict(post_data)}")
        context.log.debug(f"Post url: {url}")
        res = context.http.post(url, data=post_data)
        context.emit(data={**data, **res.serialize()})
