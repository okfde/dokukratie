import csv
import json
import logging
import sys

import click
from memorious.cli import get_crawler
from memorious.logic.context import Context
from memorious.operations.store import _get_directory_path
from mmmeta.backend.filesystem import FilesystemBackend
from mmmeta.logging import configure_logging

from .scrapers.manage import CrawlerTags

log = logging.getLogger(__name__)


@click.group()
@click.argument("crawler")
@click.pass_context
def cli(ctx, crawler, invoke_without_command=True):
    configure_logging(level=logging.INFO, out=sys.stderr)
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
@click.option(
    "--stages",
    multiple=True,
    help="stages to execute (in given order)",
    default=["clean"],
    show_default=True,
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Dry run: Don't alter json files on disk",
)
@click.option(
    "-k",
    type=(str, str),
    multiple=True,
    help="Map keys from the source json to a name used in the extraction configuration",
)
@click.option(
    "-s",
    type=(str, str),
    multiple=True,
    help="Set keys to literal values",
)
@click.option(
    "-f",
    type=(str, str),
    multiple=True,
    help="Filter for key, value pairs to only re-parse filtered data",
)
@click.pass_context
def reparse(ctx, stages, dry_run, k, s, f):
    crawler = ctx.obj["crawler"]
    log.info(f"Reparsing metadata for crawler `{crawler}` ...")
    store_stage = crawler.stages.get("store")
    context = Context(crawler, store_stage, {})
    directory = _get_directory_path(context)
    storage = FilesystemBackend(directory)
    log.info(f"Using storage: `{storage}`")
    i = 0
    x = 0
    errors = 0

    def test_filters(data, filters=f):
        for key, value in filters:
            if key not in data:
                return False
            if str(data[key]) != str(value):
                return False
        return True

    for content_hash, path in storage.get_children("", lambda x: x.endswith(".json")):
        try:
            data = storage.load_json(path)
            if test_filters(data):
                for source_key, config_key in k:
                    if source_key in data:
                        data[config_key] = data[source_key]
                for key, value in s:
                    data[key] = value
                for stage_name in stages:
                    stage = crawler.stages.get(stage_name)
                    if stage is None:
                        log.error(f"Stage `{stage_name}` not found.")
                        return
                    data = stage.method(context, data, emit=False)
                if dry_run:
                    sys.stdout.write(json.dumps(data), indent=2)
                else:
                    storage.dump_json(path, data)
                i += 1
            else:
                x += 1
        except Exception as e:
            log.error(f"Cannot reparse `{path}`: `{e}`")
            errors += 1
    log.info(f"Reparsed {i} files.")
    log.info(f"Skipped {x} files because of `-f` filter flags.")
    if errors:
        log.warn(f"{errors} errors.")
