import glob
import json
import os
import unittest
from datetime import datetime, timedelta
from itertools import product

from banal import clean_dict, ensure_list
from dateutil.parser import parse as dateparse

from dokukratie.scrapers.util import ensure_date


def get_latest_meta(scraper_name):
    with open(
        max(
            glob.glob(f"testdata/{scraper_name}/store/{scraper_name}/*.json"),
            key=os.path.getctime,
        )
    ) as f:
        data = json.load(f)
    return data


class Test(unittest.TestCase):
    def run_scraper(
        self,
        scraper_name,
        document_types=None,
        legislative_terms=None,
        start_date=None,
        end_date=None,
    ):
        base_params = {
            "TESTING_MODE": True,
            "MEMORIOUS_DEBUG": True,
            "MEMORIOUS_INCREMENTAL": False,
            "MEMORIOUS_CONFIG_PATH": "dokukratie",
            "MEMORIOUS_DATASTORE_URI": f"sqlite:///testdata/{scraper_name}/datastore.sqlite3",  # noqa
            "MEMORIOUS_HTTP_TIMEOUT": 60,
            "MEMORIOUS_BASE_PATH": f"testdata/{scraper_name}",
            "ARCHIVE_TYPE": "file",
            "ARCHIVE_PATH": "testdata/archive",
        }
        for legislative_term, document_type in product(
            ensure_list(legislative_terms) or [None],
            ensure_list(document_types) or [None],
        ):
            start_date = ensure_date(
                start_date
                or (
                    self.major_start_date
                    if "major" in (document_type or "")
                    else self.start_date
                )
            )
            end_date = ensure_date(end_date or self.end_date)
            params = clean_dict(
                {
                    "LEGISLATIVE_TERMS": legislative_term,
                    "DOCUMENT_TYPES": document_type,
                    "START_DATE": start_date.isoformat(),
                    "END_DATE": end_date.isoformat(),
                }
            )

            param_str = " ".join(
                f"{k}={v}" for k, v in {**base_params, **params}.items()
            )
            ret = os.system(f"{param_str} memorious run {scraper_name}")
            self.assertEqual(ret, 0)

            # test metadata
            data = get_latest_meta(scraper_name)
            for key in (
                "reference",
                "title",
                "document_type",
                "publisher",
                "published_at",
            ):
                self.assertIn(key, data)
            self.assertIsInstance(dateparse(data["published_at"]), datetime)
            if document_type is not None:
                self.assertEqual(data["document_type"], document_type)
            if legislative_term is None:
                self.assertGreaterEqual(
                    dateparse(data["published_at"]).date(), start_date
                )
                self.assertLessEqual(dateparse(data["published_at"]).date(), end_date)
            if legislative_term is not None:
                self.assertEqual(data["legislative_term"], legislative_term)
            if document_type in ("major_interpellation", "minor_interpellation"):
                self.assertIsInstance(data["originators"], list)
                # self.assertGreaterEqual(len(data["originators"]), 1)
                # self.assertIsInstance(data["answerers"], list)
                # self.assertGreaterEqual(len(data["answerers"]), 1)

    def setUp(self):
        self.start_date = (datetime.now() - timedelta(days=30)).date()
        self.major_start_date = self.start_date - timedelta(days=720)  # majors are rare
        self.end_date = datetime.now().date()
        scraper_name = self._testMethodName.split("_")[1]
        os.makedirs(f"./testdata/{scraper_name}", exist_ok=True)

    def test_bb(self):
        self.run_scraper("bb", document_types="generic")

    def test_bw(self):
        self.run_scraper("bw", document_types="minor_interpellation")
        # self.run_scraper("bw", document_types="major_interpellation")

    def test_by(self):
        self.run_scraper("by", document_types="minor_interpellation")
        # self.run_scraper("by", document_types="major_interpellation")

    def test_hh(self):
        self.run_scraper("hh", document_types="minor_interpellation")
        # self.run_scraper("hh", document_types="major_interpellation")

    def test_he(self):
        self.run_scraper("he", document_types="minor_interpellation")
        # self.run_scraper("he", document_types="major_interpellation")

    def test_mv(self):
        self.run_scraper("mv", document_types="minor_interpellation")
        # self.run_scraper("mv", document_types="major_interpellation")

    def test_ni(self):
        self.run_scraper("ni", document_types="minor_interpellation")
        # self.run_scraper("ni", document_types="major_interpellation")

    def test_nw(self):
        start_date = self.start_date - timedelta(days=30)  # nw has a lot unanswered
        self.run_scraper(
            "nw", document_types="minor_interpellation", start_date=start_date
        )
        # self.run_scraper("nw", document_types="major_interpellation")

    def test_rp(self):
        self.run_scraper("rp", document_types="minor_interpellation")
        # self.run_scraper("rp", document_types="major_interpellation")

    def test_st(self):
        self.run_scraper("st", document_types="minor_interpellation")
        # self.run_scraper("st", document_types="major_interpellation")

    def test_th(self):
        self.run_scraper("th", document_types="minor_interpellation")
        # self.run_scraper("th", document_types="major_interpellation")

    def test_dip(self):
        self.run_scraper("dip", document_types="minor_interpellation")
        # self.run_scraper("dip", document_types="major_interpellation")

    def test_parlamentsspiegel(self):
        self.run_scraper(
            "parlamentsspiegel",
            start_date=(datetime.now() - timedelta(days=5)).date(),
        )

    def test_sehrgutachten(self):
        self.run_scraper("sehrgutachten")
        self.run_scraper(
            "sehrgutachten",
            start_date="2020-01-01",
            end_date="2020-03-01",
        )

    # def test_vsberichte(self):
    #     self.run_scraper("vsberichte")
