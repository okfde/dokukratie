"""
manage stuff like memorious tags
"""

import logging

import dataset
from memorious import settings
from servicelayer.cache import make_key

log = logging.getLogger(__name__)


class CrawlerTags:
    def __init__(self, crawler):
        self.crawler = crawler

    def make_key(self, *key):
        return make_key(self.crawler, "tag", *key)
        return key

    def show(self, **kwargs):
        prefix = self.make_key(kwargs.pop("prefix", None))
        limit = kwargs.pop("limit")
        with dataset.connect(settings.DATASTORE_URI) as db:
            table = db[settings.TAGS_TABLE]
            rows = table.find(
                key={"like": f"{prefix}%"}, order_by="-timestamp", _limit=limit
            )
        return rows

    def delete(self, key=None, prefix=None):
        if key is None and prefix is None:
            log.info("Not deleting any tags: Neither `key` or `prefix` given.")
            return
        prefix = self.make_key(prefix)
        with dataset.connect(settings.DATASTORE_URI) as db:
            table = db[settings.TAGS_TABLE]
            res = table.delete(key={"like": f"{prefix}%"})
        return res

    def add(self, tags):
        to_insert = []
        for tag in tags:
            tag["key"] = self.make_key(tag["key"])
            to_insert.append(tag)
        with dataset.connect(settings.DATASTORE_URI) as db:
            table = db[settings.TAGS_TABLE]
            table.insert_many(to_insert)
        return len(to_insert)
