# dokukratie

A collection of scrapers to obtain documents from german parliaments and related public institutions

## usage

[installation](#installation)

To run a full scrape with the current legislative term:

    memorious run <scraper_name>

By default, documents (usually pdfs) and their metadata (json files) are stored
in `./data/<scraper_name>`

All scrapers can have these options (unless otherwise mentioned in the detailed
descriptions for each scraper) via env vars to filter the scraping.

- `DOCUMENT_TYPES` - `major_interpellation` or `minor_interpellation` (Große Anfrage / Kleine Anfrage)
- `LEGISLATIVE_TERMS` - an integer, refer to the detailed scraper description for possible values
- `START_DATE` - a date (isoformat) to scrape documents only published since this date
- `END_DATE` - a date (isoformat) to scrape documents only published until this date

For example, to scrape all minor interpellations for [Bayern](#by) from the
last (not current) legislative term but only since 2018:

    DOCUMENT_TYPES=minor_interpellation LEGISLATIVE_TERMS=17 START_DATE=2018-01-01 memorious run by

### incremental scraping

By default, scrapers are only executing requests and downloading documents they
have not seen before. To disable this behaviour, set
`MEMORIOUS_INCREMENTAL=false`

## scrapers

German state parliaments:

- [![bb](https://github.com/okfde/dokukratie/actions/workflows/bb.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/bb.yml) [bb - Landtag Brandenburg](#bb)
- [![be](https://github.com/okfde/dokukratie/actions/workflows/be.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/be.yml) [be - Abgeordnetenhaus Berlin](#be)
- [![bw](https://github.com/okfde/dokukratie/actions/workflows/bw.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/bw.yml) [bw - Landtag von Baden-Württemberg](#bw)
- [![by](https://github.com/okfde/dokukratie/actions/workflows/by.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/by.yml) [by - Bayerischer Landtag](#by)
- [![hh](https://github.com/okfde/dokukratie/actions/workflows/hh.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/hh.yml) [hh - Hamburgische Bürgerschaft](#hh)
- [![he](https://github.com/okfde/dokukratie/actions/workflows/he.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/he.yml) [he - Hessischer Landtag](#he)
- [![mv](https://github.com/okfde/dokukratie/actions/workflows/mv.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/mv.yml) [mv - Landtag Mecklenburg-Vorpommern](#mv)
- [![ni](https://github.com/okfde/dokukratie/actions/workflows/ni.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/ni.yml) [ni - Landtag Niedersachsen](#ni)
- [![rp](https://github.com/okfde/dokukratie/actions/workflows/rp.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/rp.yml) [rp - Landtag Rheinland-Pfalz](#rp)
- [![st](https://github.com/okfde/dokukratie/actions/workflows/st.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/st.yml) [st - Landtag von Sachsen-Anhalt](#st)
- [![th](https://github.com/okfde/dokukratie/actions/workflows/th.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/th.yml) [th - Thüringer Landtag](#th)

Other scrapers:

- [![dip](https://github.com/okfde/dokukratie/actions/workflows/dip.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/dip.yml) [dip - Dokumentations- und Informationssystem für Parlamentsmaterialien - API](#dip)
- [![parlamentsspiegel](https://github.com/okfde/dokukratie/actions/workflows/parlamentsspiegel.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/parlamentsspiegel.yml) [parlamentsspiegel - Parlamentsspiegel (gemeinsames Informationssystem der Landesparlamente)](#parlamentsspiegel)
- [![sehrgutachten](https://github.com/okfde/dokukratie/actions/workflows/sehrgutachten.yml/badge.svg)](https://github.com/okfde/dokukratie/actions/workflows/sehrgutachten.yml) [sehrgutachten - Gutachten der Wissenschaftlichen Dienste](#sehrgutachten)
- [vsberichte - Verfassungsschutzberichte des Bundes und der Länder](#vsberichte)


### bb

**Landtag Brandenburg**

    memorious run bb

The scraper uses the [starweb](#starweb) implementation using this form:
https://www.parlamentsdokumentation.brandenburg.de/starweb/LBB/ELVIS/servlet.starweb?path=LBB/ELVIS/LISSH.web&AdvancedSearch=yes

#### `LEGISLATIVE_TERMS`:

**current**: 7

**earliest**: 1

#### `DOCUMENT_TYPES`:

Unfortunately, Brandenburg gives no results with answers for types "Kleine
Anfrage" or "Große Anfrage", so the type option is unusable.

### be

**Abgeordnetenhaus Berlin**

    memorious run be

The backend used to be starweb, but recently (2021-06-24) changed to something
completly new, which could still be something starweb related, but according to
urls it is called "portala". The scraper still requires some refining to work
properly with date / document_type options, for now a `START_DATE` is always
required to run.

The scraper sends some json that looks like an Elasticsearch query via post to
this endpoint: https://pardok.parlament-berlin.de/portala/browse.tt.html
from a [query template](./dokukratie/scrapers/portala.query.json)

Although the new frontend looks fancy, that doesn't mean the service is
performant. With too large queries (a long date range above a few months) it
will shut down and return a 502 Error.

#### `LEGISLATIVE_TERMS`:

**current**: 18

**earliest**: 11

#### `DOCUMENT_TYPES`:

`written_interpellation` (Both "Große" and "Kleine" anfragen)



### bw

**Landtag von Baden-Württemberg**

    memorious run bw

For convenience, the scraper directly the xhr request result from this base site: https://www.landtag-bw.de/home/dokumente/drucksachen.html

Example:

https://www.landtag-bw.de/cms/render/live/de/sites/LTBW/home/dokumente/drucksachen/contentBoxes/drucksachen.xhr?limit=10&initiativeType=KA&offset=0

There is no explicit option for `LEGISLATIVE_TERMS`, but to filter for the
actual terms of BW, you can use `START_DATE` and `END_DATE` ranges that match
the terms.


#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`


### by

**Bayerischer Landtag**

    memorious run by

The scraper uses this result page: https://www.bayern.landtag.de/parlament/dokumente/drucksachen/?dokumentenart=Drucksache&anzahl_treffer=10

#### `LEGISLATIVE_TERMS`:

**current**: 18

**earliest**: 1 (but useful metadata starts at 5 [1962-66])

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`


### he

**Hessischer Landtag**

    memorious run he

The scraper uses the [starweb](#starweb) implementation using this form:
http://starweb.hessen.de/starweb/LIS/servlet.starweb?path=LIS/PdPi.web

#### `LEGISLATIVE_TERMS`:

**current**: 20

**earliest**: 14 (or: 8?) // TODO

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`

### hh

**Hamburgische Bürgerschaft**

    memorious run hh

The scraper uses the [parldok](#parldok) [5.4.1] implementation using this form:
https://www.buergerschaft-hh.de/parldok/formalkriterien

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`

#### `LEGISLATIVE_TERMS`:

**current**: 22

**earliest**: 16

### mv

**Landtag Mecklenburg-Vorpommern**

    memorious run mv

The scraper uses the [parldok](#parldok) [5.6.0] implementation using this form:
https://www.dokumentation.landtag-mv.de/parldok/formalkriterien/

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`

#### `LEGISLATIVE_TERMS`:

**current**: 7

**earliest**: 1


### ni

**Landtag Niedersachsen**

    memorious run ni

The scraper uses the [starweb](#starweb) implementation using this form:
https://www.nilas.niedersachsen.de/starweb/NILAS/servlet.starweb?path=NILAS/lissh.web

#### `LEGISLATIVE_TERMS`:

**current**: 18

**earliest**: 10

### rp

**Landtag Rheinland-Pfalz**

    memorious run rp

The scraper uses the [starweb](#starweb) implementation using this form:
https://opal.rlp.de/starweb/OPAL_extern/servlet.starweb?path=OPAL_extern/PDOKU.web

#### `LEGISLATIVE_TERMS`:

**current**: 18

**earliest**: 11

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`

### st

**Landtag von Sachsen-Anhalt**

    memorious run st

The scraper uses the [starweb](#starweb) implementation using this form:
https://padoka.landtag.sachsen-anhalt.de/starweb/PADOKA/servlet.starweb?path=PADOKA/LISSH.web&AdvancedSuche

#### `LEGISLATIVE_TERMS`:

**current**: 7

**earliest**: 1

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`

### th

**Thüringer Landtag**

    memorious run th

The scraper uses the [parldok](#parldok) [5.6.5] implementation using this form:
http://parldok.thueringen.de/ParlDok/formalkriterien/

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`

#### `LEGISLATIVE_TERMS`:

**current**: 7

**earliest**: 1

### dip

**Dokumentations- und Informationssystem für Parlamentsmaterialien - API**

    memorious run dip

There is a [really nice api](https://dip.bundestag.de/%C3%BCber-dip/hilfe/api#content).
The scraper uses this base url (with the public api key):
https://search.dip.bundestag.de/api/v1/drucksache?apikey=N64VhW8.yChkBUIJeosGojQ7CSR2xwLf3Qy7Apw464&f.zuordnung=BT

#### `DOCUMENT_TYPES`:
- `minor_interpellation`
- `major_interpellation`

### parlamentsspiegel

**Parlamentsspiegel (gemeinsames Informationssystem der Landesparlamente)**

    memorious run parlamentsspiegel

The "Parlamentsspiegel" is an official aggregator page for the document systems
of the german state parliaments.

The scraper uses this index page with configurable get parameters:
https://www.parlamentsspiegel.de/home/suchergebnisseparlamentsspiegel.html?view=kurz&sortierung=dat_desc&vorgangstyp=ANFRAGE&datumVon=15.05.2021

The "Parlamentsspiegel" doesn't distinguish between minor and major
interpellations for the requests, so the `DOCUMENT_TYPES` option is not
available.

### sehrgutachten

**Ausarbeitungen der Wissenschaftlichen Dienste des Deutschen Bundestages**

    memorious run sehrgutachten

Other than the name suggests, it's not technical based on
https://sehrgutachten.de but scrapes the website of the bundestag directly.

This scraper scrapes documents from the
[Wissenschaftliche Dienste](https://www.bundestag.de/ausarbeitungen/)
directly using and parsing this ajax call:
https://www.bundestag.de/ajax/filterlist/de/dokumente/ausarbeitungen/474644-474644/?limit=10

There is no option `DOCUMENT_TYPES` and `LEGISLATIVE_TERMS` but `START_DATE`
and `END_DATE` are available.


### vsberichte

**Verfassungsschutzberichte des Bundes und der Länder**

    memorious run vsberichte

Scraped from the api from https://vsberichte.de

This scraper doesn't need to run frequently as there is a new report once in a year.

There are no filter options available.

## technical implementation

The scrapers are based upon [memorious](https://memorious.readthedocs.io/en/latest/)

Therefore, for each scraper there is a yaml file in `./dokukratie/` that
defines how the scraper should run.

Some scrapers work with just a yaml definition, like [Bayern](#by): [`./dokukratie/by.yml`](./dokukratie/by.yml)

Some others have their own custom python implementation, like [Baden-Württemberg](#bw): [`./dokukratie/scrapers/bw.py`](./dokukratie/scrapers/bw.py)

Some others share the same software for their document database backend/frontend, mainly **starweb** or **parldok**

### starweb

Used by:
- [st](#st)
- [bb](#bb)
- be
- hb
- [he](#he)
- [ni](#ni)
- [rp](#rp)

Code: [`./dokukratie/scrapers/starweb.py`](./dokukratie/scrapers/starweb.py)

### parldok

Used by:
- [hh](#hh)
- [mv](#mv)
- [th](#th)

Code: [`./dokukratie/scrapers/parldok.py`](./dokukratie/scrapers/parldok.py)

## mmmeta

The scrapers generate a metadata database for [mmmeta](https://github.com/simonwoerpel/mmmeta) to consume.

This is useful for client applications to track state of files without
downloading the actual files, e.g. to know which files are already consumed and
to only download newer ones, etc...

How to use `mmmeta` for dokukratie:


### 1. install

Current used version: 0.4.0

    pip install mmmeta

### 2. Sync metadata and config:

    aws s3 sync s3://<bucket_name>/<scraper_name>/_mmmeta ./data/<scraper_name>

This will download the necessary metadata csv files (`./db/`) and `config.yml`

### 3. Generate or update local state:

Either use env var `MMMETA=./data/<scraper_name>` or jump into the base
directory `./data/<scraper_name>` where the subdirectory `_mmmeta` exists.

    mmmeta update

or, within python applications:

```python
from mmmeta import mmmeta

# init:
m = mmmeta()  # env var MMMETA
# OR
m = mmmeta("./data/<scraper_name>")

# update (or generate) local state
m.update()
```

If this runs into sqlalchemy migration problems, there is an attempt to fix it
(perhaps make a backup of the local `state.db` before):

    mmmeta update --cleanup

or, within python applications:

```python
m.update(cleanup=True)
```

This will cleanup data in the `state.db` according to `config.yml` but will
leave columns starting with an underscore untouched.

### 4. Access file metadata within python applications

soft delete files (not existing in the s3 bucket for some reason...) are
marked with `__deleted=1` and have a `__deleted_reason` property.

```python
for file in m.files:
    # `file` has metadata as dictionary keys, e.g.:
    publisher = file["publisher"]
    # ...

    # s3 location:
    file.remote.uri

    # alter state data, e.g.:
    # as a convention, local state data should start with _
    # to not confuse it with the remote metadata
    file["_foo"] = bar
    file["_downloaded"] = True
    file.save()
```

## installation

    make install

additional dependencies for local development:

    make install.dev

additional dependencies for production deployment (i.e. `psycopg2`):

    make install.prod

## testing

Install test utils:

    make install.test

Then,

    make test

This will run through all the scrapers (see details in
`./tests/test_scrapers.py`) with different combinations of input parameters and
stop after the first document downloaded.

Or, to test only a specific scraper:

    make test.<scraper_name>

Test all scrapers with the [starweb](#starweb) implementation:

    make test.starweb

Test all scrapers with the [parldok](#parldok) implementation:

    make test.parldok

