import click
import csv
import logging
import sys

from memorious.cli import get_crawler
from memorious.logic.context import Context
from memorious.operations.store import _get_directory_path
from mmmeta.backend.filesystem import FilesystemBackend
from mmmeta.logging import configure_logging
from mmmeta.util import casted_dict

from .scrapers.operations import clean, UNCASTED_KEYS
from .scrapers.manage import CrawlerTags

log = logging.getLogger(__name__)


@click.group()
@click.argument("crawler")
@click.pass_context
def cli(ctx, crawler, invoke_without_command=True):
    configure_logging(level=logging.INFO)
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["crawler"] = get_crawler(crawler)


@cli.group()
@click.pass_context
def tags(ctx):
    pass


@tags.command(help="Show tags")
@click.option("--prefix", help="key prefix, eg.: `skip_incremental`")
@click.option("--limit")
@click.option("--header/--no-header", show_default=True, default=True)
@click.pass_context
def show(ctx, prefix, limit, header):
    tags = CrawlerTags(ctx.obj["crawler"])
    writer = csv.DictWriter(sys.stdout, fieldnames=("timestamp", "key", "value"))
    if header:
        writer.writeheader()
    for row in tags.show(prefix=prefix, limit=limit):
        writer.writerow(row)


@tags.command(help="Delete tags (list of keys from stdin)")
@click.option("--prefix", help="key prefix, eg.: `skip_incremental`")
@click.pass_context
def delete(ctx, prefix):
    tags = CrawlerTags(ctx.obj["crawler"])
    res = tags.delete(prefix=prefix)
    if res:
        log.info("Deleted some tags.")


@tags.command(help="Add tags (csv from stdin)")
@click.pass_context
def add(ctx):
    tags = CrawlerTags(ctx.obj["crawler"])
    reader = csv.DictReader(sys.stdin)
    res = tags.add(reader)
    log.info(f"Added {res} tags.")


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
