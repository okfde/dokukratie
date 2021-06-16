export MEMORIOUS_CONFIG_PATH=dokukratie
export MEMORIOUS_USER_AGENT="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"

# production use: `make <crawler>`
# current available scrapers:
# state scrapers
bb: bb.pull bb.run_prod bb.mmmeta bb.upload
bw: bw.pull bw.run_prod bw.mmmeta bw.upload
by: by.pull by.run_prod by.mmmeta by.upload
hh: hh.pull hh.run_prod hh.mmmeta hh.upload
he: he.pull he.run_prod he.mmmeta he.upload
mv: mv.pull mv.run_prod mv.mmmeta mv.upload
ni: ni.pull ni.run_prod ni.mmmeta ni.upload
nw: nw.pull nw.run_prod nw.mmmeta nw.upload
rp: rp.pull rp.run_prod rp.mmmeta rp.upload
st: st.pull st.run_prod st.mmmeta st.upload

th: th.pull th.run_prod th.mmmeta th.upload

# other scrapers
dip: dip.pull dip.run_prod dip.mmmeta dip.upload
parlamentsspiegel: parlamentsspiegel.pull parlamentsspiegel.run_prod parlamentsspiegel.mmmeta parlamentsspiegel.upload
sehrgutachten: sehrgutachten.pull sehrgutachten.run_prod sehrgutachten.mmmeta sehrgutachten.upload
vsberichte: vsberichte.pull vsberichte.run_prod vsberichte.mmmeta vsberichte.upload

he.run_prod:
	# don't ddos hessen
	MEMORIOUS_HTTP_RATE_LIMIT=30 MMMETA=./data/store/he memorious run he --threads=4

parlamentsspiegel.run_prod:
	# don't go back too far
	START_DATE_DELTA=2 MMMETA=./data/store/parlamentsspiegel memorious run parlamentsspiegel --threads=4

vsberichte.run_prod:
	# don't use mmmeta
	memorious run vsberichte --threads=4


%.run_prod:
	MMMETA=./data/store/$* memorious run $* --threads=4

run.%:
	memorious run $*

install:
	pip install -e .

install.dev: install
	pip install -r requirements-dev.txt

install.prod: install
	pip install -r requirements-prod.txt

install.test: install.dev
	pip install twine coverage nose moto pytest pytest-cov black flake8 isort

%.config:
	mkdir -p ./data/store/$*/_mmmeta
	sed "s/<scraper_name>/$*/" config.yml.tmpl > ./data/store/$*/_mmmeta/config.yml

%.action:
	mkdir -p ./.github/workflows/
	sed "s/<scraper_name>/$*/" workflow.yml.tmpl > ./.github/workflows/$*.yml

%.mmmeta:
	MMMETA=./data/store/$* mmmeta generate

%.pull:
	aws s3 sync s3://$(DATA_BUCKET)/$*/_mmmeta/db/ ./data/store/$*/_mmmeta/db

%.push:
	aws s3 sync --exclude "*.db*" ./data/store/$*/_mmmeta/ s3://$(DATA_BUCKET)/$*/_mmmeta

%.upload:
	aws s3 sync --exclude "*.db*" ./data/store/$*/ s3://$(DATA_BUCKET)/$*

test:
	rm -rf testdata
	mkdir testdata
	pytest -s --cov=dokukratie --cov-report term-missing ./tests/
	rm -rf testdata


test.%:
	rm -rf testdata/$*
	mkdir -p testdata/$*
	pytest -s --cov=dokukratie --cov-report term-missing ./tests/ -k "test_$*"
	rm -rf testdata/$*

clean:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

redis:
	docker run -p 6379:6379 redis:alpine
