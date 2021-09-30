import glob
import json
import os
import time
import unittest
from datetime import datetime, timedelta
from itertools import product
from pprint import pformat

from banal import clean_dict, ensure_list
from dateutil.parser import parse as dateparse
from memorious_extended.util import ensure_date
from servicelayer import env


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
        **additional_envs,
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
                env.get("START_DATE", start_date)
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
                f"{k}={v}"
                for k, v in {**base_params, **params, **additional_envs}.items()
            )

            print("env:", pformat(param_str))

            ret = os.system(f"{param_str} memorious run {scraper_name}")
            self.assertEqual(ret, 0)

            # test metadata
            data = get_latest_meta(scraper_name)

            print(pformat(data))

            for key in (
                "reference",
                "title",
                "document_type",
                "publisher",
                "published_at",
            ):
                self.assertIn(key, data)
            for key in ("type", "name", "url", "jurisdiction"):
                self.assertIn(key, data["publisher"])
            for key in ("id", "name"):
                self.assertIn(key, data["publisher"]["jurisdiction"])
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

            if "interpellation" in data["document_type"]:
                self.assertIn("originators", data)
                self.assertIsInstance(data["originators"], list)
                self.assertGreaterEqual(len(data["originators"]), 1)
                for o in data["originators"]:
                    self.assertIsInstance(o, dict)
                    # either "name" or "party" should be in dict:
                    self.assertLessEqual(len(set(("name", "party")) - set(o.keys())), 2)
                self.assertIn("answerers", data)

    def setUp(self):
        self.start_date = (datetime.now() - timedelta(days=30)).date()
        self.major_start_date = self.start_date - timedelta(days=720)  # majors are rare
        self.end_date = datetime.now().date()
        scraper_name = self._testMethodName.split("_")[1]
        os.makedirs(f"./testdata/{scraper_name}", exist_ok=True)

    def test_bb(self):
        self.run_scraper("bb", document_types="interpellation")
        self.run_scraper(
            "bb",
            document_types="interpellation",
            legislative_terms=6,
            start_date="2014-09-14",
            end_date="2015-01-14",
        )
        self.run_scraper(
            "bb",
            document_types="interpellation",
            legislative_terms=4,
            start_date="2004-09-19",
            end_date="2005-01-19",
        )
        self.run_scraper(
            "bb",
            document_types="interpellation",
            legislative_terms=1,
            start_date="1990-10-14",
            end_date="1991-01-14",
        )

    def test_be(self):
        self.run_scraper("be", document_types="interpellation")
        self.run_scraper(
            "be",
            document_types="minor_interpellation",
            legislative_terms=17,
            start_date="2012-01-01",
            end_date="2012-06-01",
        )
        self.run_scraper(
            "be",
            document_types="minor_interpellation",
            legislative_terms=13,
            start_date="1996-01-01",
            end_date="1996-06-01",
        )
        self.run_scraper(
            "be",
            document_types="minor_interpellation",
            legislative_terms=11,
            start_date="1990-01-01",
            end_date="1990-06-01",
        )

    def test_bw(self):
        self.run_scraper(
            "bw",
            document_types="minor_interpellation",
            start_date="2021-01-01",
            end_date="2021-06-01",
        )
        self.run_scraper(
            "bw",
            document_types="minor_interpellation",
            legislative_terms=16,
            start_date="2017-01-01",
            end_date="2017-06-01",
        )
        self.run_scraper(
            "bw",
            document_types="minor_interpellation",
            legislative_terms=12,
            start_date="1998-01-01",
            end_date="1998-06-01",
        )
        self.run_scraper(
            "bw",
            document_types="minor_interpellation",
            legislative_terms=9,
            start_date="1985-01-01",
            end_date="1985-06-01",
        )
        # self.run_scraper("bw", document_types="major_interpellation")

    def test_by(self):
        self.run_scraper(
            "by", legislative_terms=18, document_types="minor_interpellation"
        )
        self.run_scraper(
            "by",
            legislative_terms=15,
            document_types="minor_interpellation",
            start_date="2005-01-01",
            end_date="2005-06-01",
        )
        self.run_scraper(
            "by",
            legislative_terms=8,
            document_types="minor_interpellation",
            start_date="1975-01-01",
            end_date="1975-06-01",
        )
        self.run_scraper(
            "by",
            legislative_terms=5,
            document_types="minor_interpellation",
            start_date="1964-01-01",
            end_date="1964-06-01",
        )
        # self.run_scraper("by", document_types="major_interpellation")

    def test_hb(self):
        self.run_scraper(
            "hb",
            document_types="minor_interpellation",
            start_date="2021-05-01",
            MEMORIOUS_RATE_LIMIT=10,  # be careful with bremen!
        )
        # self.run_scraper("hh", document_types="major_interpellation")

    def test_hh(self):
        self.run_scraper("hh", document_types="minor_interpellation")
        self.run_scraper(
            "hh",
            document_types="minor_interpellation",
            legislative_terms=20,
            start_date="2012-01-01",
            end_date="2012-06-01",
        )
        self.run_scraper(
            "hh",
            document_types="minor_interpellation",
            legislative_terms=16,
            start_date="2000-01-01",
            end_date="2000-06-01",
        )
        # self.run_scraper("hh", document_types="major_interpellation")

    def test_he(self):
        self.run_scraper(
            "he", document_types="minor_interpellation", start_date="2021-01-01"
        )
        # self.run_scraper(
        #     "he",
        #     document_types="minor_interpellation",
        #     legislative_terms="WP19",
        #     start_date="2016-01-01",
        # )
        # self.run_scraper("he", document_types="major_interpellation")

    def test_mv(self):
        self.run_scraper("mv", document_types="minor_interpellation")
        self.run_scraper(
            "mv",
            document_types="minor_interpellation",
            legislative_terms=4,
            start_date="2004-01-01",
            end_date="2004-06-01",
        )
        # self.run_scraper(
        #     "mv",
        #     document_types="minor_interpellation",
        #     legislative_terms=1,
        #     start_date="1990-01-01",
        #     end_date="1994-06-01",
        # )
        # self.run_scraper("mv", document_types="major_interpellation")

    def test_ni(self):
        self.run_scraper(
            "ni", document_types="minor_interpellation", MEMORIOUS_RATE_LIMIT=10
        )
        print("waiting for ni to recover...")
        time.sleep(30)
        self.run_scraper(
            "ni",
            document_types="minor_interpellation",
            legislative_terms=15,
            start_date="2004-01-01",
            end_date="2004-06-01",
            MEMORIOUS_RATE_LIMIT=10,
        )
        print("waiting for ni to recover...")
        time.sleep(30)
        self.run_scraper(
            "ni",
            document_types="minor_interpellation",
            legislative_terms=12,
            start_date="1992-01-01",
            end_date="1992-06-01",
            MEMORIOUS_RATE_LIMIT=10,
        )
        print("waiting for ni to recover...")
        time.sleep(30)
        self.run_scraper(
            "ni",
            document_types="minor_interpellation",
            legislative_terms=10,
            start_date="1985-01-01",
            end_date="1985-06-01",
            MEMORIOUS_RATE_LIMIT=10,
        )
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

    def test_sh(self):
        self.run_scraper("sh", document_types="minor_interpellation")
        # self.run_scraper("sh", document_types="major_interpellation")

    def test_st(self):
        self.run_scraper("st", document_types="minor_interpellation")
        # self.run_scraper("st", document_types="major_interpellation")

    def test_sl(self):
        self.run_scraper("sl", document_types="minor_interpellation")
        # self.run_scraper("sl", document_types="major_interpellation")

    def test_sn(self):
        self.run_scraper("sn", document_types="minor_interpellation")
        # self.run_scraper("sn", document_types="major_interpellation")

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

    def test_vsberichte(self):
        self.run_scraper("vsberichte", start_date="2020-01-01")
