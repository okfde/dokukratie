import json

from memorious.operations.parse import parse_for_metadata

from .base import BaseScraper
from .incremental import skip_incremental
from .util import get_value_from_xp as x


class PortalaScraper(BaseScraper):
    skip_incremental_config = {"key": {"data": "url"}, "target": {"stage": "store"}}

    def emit_search(self, data):
        """
        do a post request to the search overview page for given
        legislative_term and document_type to get report_id
        """

        with open(self.context.params["query_template"]) as f:
            query = f.read()

        query = query % data
        query = json.loads(query)

        data["headers"]["Referer"] = data["url"]
        res = self.context.http.post(
            self.context.params["url"], json=query, headers=data["headers"]
        )

        self.context.log.info("Search [%s]: %s" % (res.status_code, res.url))
        self.context.emit(data={**data, **res.serialize()})

    def emit_fetch_results(self, data):
        item_count = int(data["item_count"])
        start = data.get("start", 0)
        chunksize = self.context.params.get("chunksize", 50)
        report_id = data["report_id"]
        url = self.context.params["url"]
        res = self.context.http.get(
            url, params={"report_id": report_id, "start": start, "chunksize": chunksize}
        )
        self.context.emit(data={**data, **res.serialize()})
        if start + chunksize < item_count:
            self.context.log.info(f"Paginate: {start + chunksize}")
            self.context.recurse(data={**data, **{"start": start + chunksize}})

    def emit_parse_results(self, data):
        """
        parse the result list page and look for entries
        emit the detail urls for each entry and some metadata

        params in yaml config:
            optional:
                meta: dict for extracting metadata (key: xpath) that will
                      passed to the next stages
        """
        res = self.context.http.rehash(data)

        for item in res.html.xpath(self.context.params["item"]):
            data["url"] = x(item, self.context.params["download_url"])
            if not skip_incremental(
                self.context, data, self.skip_incremental_config, test_loops=3
            ):
                parse_for_metadata(self.context, data, item)
                self.context.emit("download", data=data)


# actual used stages for pipeline defined in yaml config


def init(context, data):
    scraper = PortalaScraper(context)
    scraper.emit_configuration()


def search(context, data):
    scraper = PortalaScraper(context)
    scraper.emit_search(data)


def fetch_results(context, data):
    scraper = PortalaScraper(context)
    scraper.emit_fetch_results(data)


def parse_results(context, data):
    scraper = PortalaScraper(context)
    scraper.emit_parse_results(data)
