import re

from banal import ensure_dict
from memorious import settings
from servicelayer.cache import make_key

from .util import get_value_from_xp as x


def skip_incremental(context, data):
    """
    a more advanced skip_incremental implementation

    based on a "target" that should be reached, like storing a pdf,
    the scraper should incrementally skip before if the target was
    already reached

    the data is passed along the pipeline and if the target stage
    was executed successfully, it will set the tag key

    params:
      skip_incremental:
        key:  # generate tag key based on xpath, data dict or urlpattern
            data: ... (default: reference)
            xpath: ...
            urlpattern: ...
        target:
            stage: store
    """
    if "skip_incremental" not in context.params:
        return False

    get_key = ensure_dict(context.params["skip_incremental"].get("key"))
    identifier = data.get(get_key.get("data", "reference"))
    if identifier is None:
        urlpattern = get_key.get("urlpattern")
        if urlpattern is not None:
            url = data.get("url", "")
            if re.match(urlpattern, url):
                identifier = url
    if identifier is None:
        xpath = get_key.get("xpath")
        if xpath is not None:
            res = context.http.rehash(data)
            if hasattr(res, "html"):
                identifier = x(xpath, res.html)

    if identifier is not None:
        target = context.params["skip_incremental"]["target"]
        target_key = make_key("skip_incremental", identifier, target["stage"])
        if context.check_tag(target_key):
            # we reached the target
            if settings.INCREMENTAL:
                context.log.debug("Skipping: %s" % target_key)
                return True

        # set key regardless of INCREMENTAL setting for next run
        data["skip_incremental"] = {"target": target["stage"], "key": target_key}
