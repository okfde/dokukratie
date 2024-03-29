from pprint import pformat
from urllib.parse import urljoin

from banal import clean_dict, ensure_dict, ensure_list
from furl import furl
from memorious.operations.parse import parse_for_metadata
from memorious_extended.forms import get_form
from memorious_extended.incremental import skip_incremental, skip_while_testing
from memorious_extended.util import get_value_from_xp as x
from memorious_extended.util import re_first

from .base import BaseScraper


class StarwebScraper(BaseScraper):
    skip_incremental = True
    form_xp = './/form[@name="__form"]'

    def emit_search(self, data):
        """
        do a post request to the search overview page for given legislative_term
        and document_type
        session must be initialized befor with a get request

        pass altered data["formdata"] for pagination
        """

        # formdata from existing session
        res = self.context.http.rehash(data)
        form_url, formdata = get_form(self.context, res.html, self.form_xp)

        if form_url is not None and formdata is not None:
            if "formdata" in data:
                # update formdata from previous stage if recursive during paginating
                formdata.update(data["formdata"])
            else:
                # or initialize for first search:
                # fill in legislative term / document type and dates
                # into the right fields
                for key, field in ensure_dict(
                    self.context.params.get("fields")
                ).items():
                    if key in data:
                        formdata[field] = data[key]

                # add initial formdata for search
                for field, value in ensure_dict(
                    self.context.params.get("formdata")
                ).items():
                    formdata[field] = value

            # do the post search and emit to next stage
            self.context.log.debug(f"Using formdata: {pformat(clean_dict(formdata))}")
            res = self.context.http.post(form_url, data=formdata)
            self.context.emit(data={**data, **res.serialize()})

    def emit_parse_results(self, data):
        """
        parse and yield detail items

        required parameters in yaml config:
            item - xpath for detail item
                (used as parent node for all other xpaths used within this function)
            download_url - xpath for the download url
        optional:
            next_page_formdata - dict to pass into form to execute pagination
            meta - dict of key, values for extracting metadata
        """

        res = self.context.http.rehash(data)
        for item in res.html.xpath(self.context.params["item"]):
            detail_data = {}
            parse_for_metadata(self.context, detail_data, item)

            if self.version == "5.9.1":  # WTF
                params = x(item, self.context.params["detail_params"])
                params = re_first(r"(WP=\d{1,2}\sAND\sR=\d+)", params)
                url = (
                    furl(self.context.params["detail_url"])
                    .add({"search": params})
                    .url  # noqa
                )
            else:
                url = x(item, self.context.params["download_url"])

            if url:
                for url in ensure_list(url):
                    if not url.startswith("http"):
                        url = urljoin(data["url"], f"/{url}")
                    detail_data["url"] = detail_data["source_url"] = url

                    data = {**data, **detail_data}

                    # only fetch new documents unless `MEMORIOUS_INCREMENTAL=false`
                    if not skip_incremental(self.context, data, self.skip_incremental):
                        self.context.emit(data=data)

        # pagination
        next_page = self.context.params.get("next_page")
        if next_page:
            if res.html.xpath(next_page["xpath"]):
                _, data["formdata"] = get_form(self.context, res.html, self.form_xp)
                data["formdata"].update(ensure_dict(next_page.get("formdata")))
                page = data.get("page", 1) + 1
                data["page"] = page
                if not skip_while_testing(self.context, key="paginate"):  # testing
                    self.context.log.info("Next page: %s" % page)
                    self.context.emit("next_page", data=data)


# actual stages for pipeline


def search(context, data):
    scraper = StarwebScraper(context)
    scraper.emit_search(data)


def parse_results(context, data):
    scraper = StarwebScraper(context)
    scraper.emit_parse_results(data)
