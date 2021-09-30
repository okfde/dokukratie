from datetime import datetime
from itertools import product
from pprint import pformat

from banal import clean_dict, ensure_dict, ensure_list
from furl import furl
from memorious_extended.util import ensure_date, generate_url
from memorious_extended.util import get_env_or_context as _geoc

from ..helpers.mmmeta import get_start_date


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
        context.log.debug(f"Using parameters:\n{pformat(data)}")
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

        # add scraper metadata
        data["publisher"] = context.crawler.config["publisher"]
        data["dataset_id"] = context.crawler.name
        data["dataset_label"] = context.crawler.description
        if "scraper" in context.crawler.config:
            data["scraper"] = context.crawler.config["scraper"]

        context.emit(data=data)
