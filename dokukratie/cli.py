import click
import logging

from memorious.cli import get_crawler
from memorious.logic.context import Context
from memorious.operations.store import _get_directory_path
from mmmeta.backend.filesystem import FilesystemBackend
from mmmeta.util import casted_dict

from .scrapers.operations import clean, UNCASTED_KEYS

log = logging.getLogger(__name__)


@click.group()
@click.argument("crawler")
@click.pass_context
def cli(ctx, crawler, invoke_without_command=True):
    logging.basicConfig(level=logging.INFO)
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["crawler"] = get_crawler(crawler)


@cli.command(help="Re-parse metadata for given crawler")
@click.pass_context
def reparse(ctx):
    crawler = ctx.obj["crawler"]
    log.info(f"Reparsing metadata for crawler `{crawler}` ...")
    stage = crawler.stages.get("clean")
    if stage is None:
        log.error("No clean stage found.")
        return
    context = Context(crawler, stage, {})
    directory = _get_directory_path(context)
    storage = FilesystemBackend(directory)
    log.info(f"Using storage: `{storage}`")
    i = 0
    errors = 0
    for content_hash, path in storage.get_children("", lambda x: x.endswith(".json")):
        try:
            data = storage.load_json(path)
            data = casted_dict(data, ignore_keys=UNCASTED_KEYS)
            data = clean(context, data, emit=False)
            storage.dump_json(path, data)
            i += 1
        except Exception as e:
            log.error(f"Cannot reparse `{path}`: `{e}`")
            errors += 1
    log.info(f"Reparsed {i} files.")
    if errors:
        log.warn(f"{errors} errors.")
