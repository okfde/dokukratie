from urllib.parse import urljoin

from memorious.operations.parse import parse_for_metadata
from memorious_extended.incremental import skip_incremental
from memorious_extended.util import get_value_from_xp as x
from memorious_extended.util import re_first

from .base import BaseScraper


class ParldokScraper(BaseScraper):
    skip_incremental = True

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
            detail_data = {}
            parse_for_metadata(self.context, detail_data, item)

            url = x(item, self.context.params["detail_url"])
            if self.version < "5.6.5":
                url = re_first(r".*href='([\w\/\d]+)'.*", url)

            if url:
                if not url.startswith("http"):
                    url = urljoin(data["url"], url)
                detail_data["url"] = detail_data["source_url"] = url

                data = {**data, **detail_data}
                # only fetch new documents unless `MEMORIOUS_INCREMENTAL=false`
                if not skip_incremental(
                    self.context, data, self.skip_incremental, test_loops=3
                ):
                    self.context.emit("fetch", data=data)

    def emit_next_page(self, data):
        """
        look for "next page" links and emit the first one that is higher than
        the actual page
        """
        res = self.context.http.rehash(data)
        current_page = data.get("page", 1)

        for next_page_url in res.html.xpath(self.context.params["next_page"]):

            if self.version == "5.6.5":
                next_page_url = re_first(r".*href='([\w\/\d]+)'.*", next_page_url)

            next_page = int(next_page_url.split("/")[-1])
            if next_page > current_page:
                self.context.log.info("Next page: %s" % next_page)
                self.context.emit(
                    "next_page",
                    data={
                        **data,
                        **{
                            "url": urljoin(self.base_url, next_page_url),
                            "page": next_page,
                        },
                    },
                )
                return


# actual used stages for pipeline defined in yaml config


def parse_results(context, data):
    scraper = ParldokScraper(context)
    scraper.emit_parse_results(data)
    scraper.emit_next_page(data)
