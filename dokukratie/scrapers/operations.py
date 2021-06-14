import re
from itertools import product

from banal import clean_dict, ensure_dict, ensure_list
from furl import furl
from memorious.helpers.rule import Rule
from memorious.operations.fetch import fetch as memorious_fetch
from memorious.operations.parse import parse_for_metadata, parse_html
from memorious.operations.store import directory as memorious_store
from mmmeta.util import casted_dict
from servicelayer import env

from .exceptions import MetaDataError, RegexError
from .incremental import skip_incremental
from .mmmeta import get_start_date
from .util import re_first  # , skip_while_testing
from .util import ensure_date, flatten_dict
from .util import get_env_or_context as _geoc


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
    if start_date is None:
        start_date = ensure_date(get_start_date(context))

    if start_date is not None:
        start_date = start_date.strftime(dateformat)
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
        url = context.params.get("url")
        if url:
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
    """

    if not skip_incremental(context, data):
        with context.http.rehash(data) as result:
            if result.html is not None:
                # Get extra metadata from the DOM
                parse_for_metadata(context, data, result.html)
                # maybe data is updated with unique identifier for incremental skip
                if not skip_incremental(context, data):
                    parse_html(context, data, result)

            rules = context.params.get("store") or {"match_all": {}}
            if Rule.get_rule(rules).apply(result):
                context.emit(rule="store", data=data)


def fetch(context, data):
    """
    an extended fetch to be able to skip_incremental based on passed data dict
    """
    if not skip_incremental(context, data):
        memorious_fetch(context, data)


DELETE_KEYS = ("page", "formdata")

# don't apply typing here:
UNCASTED_KEYS = ("modified_at", "retrieved_at", "reference")

# ensure lists
LISTISH_KEYS = ("originators", "answerers")

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
        for key, patterns in ensure_dict(context.params.get("extractors")).items():
            if not isinstance(data.get(key), str):
                # already parsed
                continue
            value = None
            patterns = ensure_list(patterns)
            for pattern in patterns:
                pattern = re.compile(pattern)  # yaml foo
                try:
                    value = re_first(pattern, data[key])
                    if value is not None:
                        data[key] = value
                        break
                except RegexError:
                    pass
            # still nothing found:
            if value is None:
                context.log.warning(
                    "Can't extract metadata for `%s`: [%s] %s"
                    % (key, pattern.pattern, data[key])
                )
                data[f"{key}__unparsed"] = data[key]
                data[key] = None

        # clean some values
        for key, values in ensure_dict(context.params.get("values")).items():
            if data.get(key) in values:
                data[key] = values[data[key]]

    # ensure document id metadata
    if "reference" in data:
        data["reference"] = re_first(r"\d{1,2}\/\d+", data["reference"])
        data["legislative_term"], data["document_id"] = data["reference"].split("/")
    elif "document_id" in data and "legislative_term" in data:
        data["reference"] = "{legislative_term}/{document_id}".format(**data)
    else:
        raise MetaDataError(
            "Either `reference` or `legislative_term` and `document_id` must be present in metadata"  # noqa
        )

    # unique foreign id accross all scrapers:
    data["foreign_id"] = "%s-%s" % (
        data["publisher"]["jurisdiction"]["id"],
        data["reference"],
    )

    # cleanup and type
    for key in DELETE_KEYS:
        if key in data:
            del data[key]
    for key in LISTISH_KEYS:
        if key in data:
            data[key] = ensure_list(data[key])
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
    an extended store to be able to set skip_incremental and quit the scraper
    after first store during test run
    """
    memorious_store(context, data)
    incremental = ensure_dict(data.get("skip_incremental"))
    if incremental.get("target") == context.stage.name:
        if incremental.get("key") is not None:
            context.set_tag(incremental["key"], True)
    if env.to_bool("TESTING_MODE"):
        context.crawler.cancel()
        context.log.debug("Cancelling crawler run because of test mode.")


def parse_json(context, data):
    """
    parse a json response and yield data dict based on config

    key path are dot notation
    """
    res = context.http.rehash(data)
    jsondata = clean_dict(flatten_dict(res.json))
    for key, path in ensure_dict(context.params).items():
        data[key] = jsondata[path]
    context.emit(data=data)
