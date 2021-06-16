import re

from banal import ensure_dict
from memorious import settings
from servicelayer import env
from servicelayer.cache import make_key

from .util import get_value_from_xp as x


def should_skip_incremental(context, data, config=None):
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

    (can also be passed in as dict for config parameter)
    """
    if config is None and "skip_incremental" not in context.params:
        return False

    config = ensure_dict(config or context.params.get("skip_incremental"))
    get_key = ensure_dict(config.get("key"))
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
        target = config.get("target", {"stage": "store"})  # FIXME
        target_key = make_key("skip_incremental", identifier, target["stage"])
        if context.check_tag(target_key):
            # we reached the target
            if settings.INCREMENTAL:
                context.log.debug("Skipping: %s" % target_key)
                return True

        # set key regardless of INCREMENTAL setting for next run
        data["skip_incremental"] = {"target": target["stage"], "key": target_key}


def skip_while_testing(context, stage=None, key=None, counter=-1):
    # try to speed up tests...
    if not env.to_bool("TESTING_MODE"):
        return False

    key = make_key(
        "skip_while_testing",
        context.crawler,
        stage or context.stage,
        context.run_id,
        key,
    )
    tag = context.get_tag(key)
    if tag is None:
        context.set_tag(key, 0)
        return False
    if tag >= counter:
        context.log.debug("Skipping: %s" % key)
        return True
    context.set_tag(key, tag + 1)


def skip_incremental(
    context,
    data,
    config=None,
    previous_stage_test_runs=1,
    current_stage_test_runs=1,
    test_loops=None,
):
    """
    set up some incremental logic and pass through skip_incremental

    testing logic:
    if the "current" stage is reached X times, the "previous" will be marked
    as to skip for all next executions to speed up test run
    """
    # production use of skip_incremental
    if should_skip_incremental(context, data, config):
        return True

    if env.to_bool("TESTING_MODE"):
        # we reached the last stage?
        if data.get("skip_incremental", {}).get("target") == context.stage.name:
            context.log.debug("Cancelling crawler run because of test mode.")
            context.crawler.cancel()
            return

        # track recursion
        recursion = data.get(f"{context.stage}_recursion", 0)
        if test_loops is None:
            recursion += 1
        data[f"{context.stage}_recursion"] = recursion
        context.log.debug(f"{context.stage} recursion: {recursion}")
        previous_stage = data["previous_stage"] = data.get("current_stage")
        current_stage = data["current_stage"] = context.stage.name

        previous_finished = False
        current_finished = False

        if previous_stage is not None:
            # update counting for previous stage
            previous_recursion = data.get(f"{previous_stage}_recursion", 0)
            previous_finished = skip_while_testing(
                context, previous_stage, previous_recursion, previous_stage_test_runs
            )
            if previous_finished:
                context.log.debug(
                    f"Testing: finished stage `{previous_stage}_{previous_recursion}`"
                )

        if previous_stage is None or previous_finished:
            # update counting for current stage
            current_finished = skip_while_testing(
                context, current_stage, recursion, current_stage_test_runs
            )
        return current_finished
