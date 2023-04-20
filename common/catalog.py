import json
import yaml
import requests
from typing import Optional
from datetime import datetime
from nomenklatura.dataset import DataCatalog
from nomenklatura.util import PathLike, datetime_iso
from zavod.dataset import ZavodDataset


def build_catalog(catalog_in: PathLike):
    with open(catalog_in, "r") as fh:
        catalog_in_data = yaml.safe_load(fh)
    catalog = DataCatalog(ZavodDataset, {})
    catalog.updated_at = datetime_iso(datetime.utcnow())
    for ds_data in catalog_in_data["datasets"]:
        include_url: Optional[str] = ds_data.pop("include", None)
        if include_url is not None:
            try:
                resp = requests.get(include_url)
                ds_data = resp.json()
            except Exception as exc:
                print("ERROR [%s]: %s" % (include_url, exc))
                continue
        ds = catalog.make_dataset(ds_data)
        print("Dataset: %r" % ds)

    with open("catalog.json", "w") as fh:
        json.dump(catalog.to_dict(), fh)


if __name__ == "__main__":
    build_catalog("catalog.in.yml")
