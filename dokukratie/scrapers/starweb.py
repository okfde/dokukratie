from banal import ensure_dict
from memorious.operations.parse import parse_for_metadata

from .util import get_value_from_xp as x
from .incremental import skip_incremental
from .base import BaseScraper


class StarwebScraper(BaseScraper):
    def get_formdata(self, html, form_xp='.//form[@name="__form"]'):
        """
        return action, data
        """
        form = html.find(form_xp)
        return x(form, "@action"), {
            **{i.name: i.value for i in form.findall(".//input")},
            **{i.name: i.value for i in form.findall(".//select")},
        }

    def emit_search(self, data):
        """
        do a post request to the search overview page for given legislative_term
        and document_type
        session must be initialized befor with a get request

        pass altered data["formdata"] for pagination
        """

        # formdata from existing session
        res = self.context.http.rehash(data)
        form_url, formdata = self.get_formdata(res.html)

        if "formdata" in data:
            # update formdata from previous stage if recursive during paginating
            formdata.update(data["formdata"])
        else:
            # or initialize for first search:
            # fill in legislative term / document type and dates into the right fields
            for key, field in ensure_dict(self.context.params.get("fields")).items():
                if key in data:
                    formdata[field] = data[key]

            # add initial formdata for search
            for field, value in ensure_dict(
                self.context.params.get("formdata")
            ).items():
                formdata[field] = value

        # do the post search and emit to next stage
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
            detail_data["url"] = x(item, self.context.params["download_url"])

            # only fetch new documents unless `MEMORIOUS_INCREMENTAL=false`
            if not skip_incremental(self.context, detail_data):
                self.context.emit("download", data={**data, **detail_data})

        # pagination
        next_page = self.context.params.get("next_page")
        if next_page:
            if res.html.xpath(next_page["xpath"]):
                _, data["formdata"] = self.get_formdata(res.html)
                data["formdata"].update(ensure_dict(next_page.get("formdata")))
                page = data.get("page", 1) + 1
                data["page"] = page
                self.context.log.info("Next page: %s" % page)
                self.context.emit("next_page", data=data)

    def emit_post(self, data):
        """
        a helper to perform some weird navigating post requests for initializing
        for some isntances of starweb
        """

        res = self.context.http.rehash(data)
        form_url, formdata = self.get_formdata(res.html)
        formdata.update(ensure_dict(self.context.params.get("formdata")))
        res = self.context.http.post(form_url, data=formdata)
        self.context.emit(data={**data, **res.serialize()})


# actual stages for pipeline


def init(context, data):
    scraper = StarwebScraper(context)
    scraper.emit_configuration()


def search(context, data):
    scraper = StarwebScraper(context)
    scraper.emit_search(data)


def parse_results(context, data):
    scraper = StarwebScraper(context)
    scraper.emit_parse_results(data)


def post(context, data):
    scraper = StarwebScraper(context)
    scraper.emit_post(data)
