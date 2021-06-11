export MEMORIOUS_CONFIG_PATH=dokukratie

# production use
sehrgutachten: sehrgutachten.pull sehrgutachten.run_prod sehrgutachten.mmmeta sehrgutachten.upload
st: st.pull st.run_prod st.mmmeta st.upload
bw: bw.pull bw.run_prod bw.mmmeta bw.upload
th: th.pull th.run_prod th.mmmeta th.upload
mv: mv.pull mv.run_prod mv.mmmeta mv.upload
hh: hh.pull hh.run_prod hh.mmmeta hh.upload
by: by.pull by.run_prod by.mmmeta by.upload

%.run_prod:
	START_DATE_DELTA=14 MMMETA=./data/store/$* memorious run $* --threads=4

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

# current available scrapers:
config: bw.config by.config hh.config mv.config st.config th.config
action: bw.action by.action hh.action mv.action st.action th.action
mmmeta: bw.mmmeta by.mmmeta hh.mmmeta mv.mmmeta st.mmmeta th.mmmeta dip.mmmeta sehrgutachten.mmmeta parlamentsspiegel.mmmeta vsberichte.mmmeta
pull: bw.pull by.pull hh.pull mv.pull st.pull th.pull dip.pull sehrgutachten.pull parlamentsspiegel.pull vsberichte.pull
push: bw.push by.push hh.push mv.push st.push th.push dip.push sehrgutachten.push parlamentsspiegel.push vsberichte.push
upload: bw.upload by.upload hh.upload mv.upload st.upload th.upload dip.upload sehrgutachten.upload parlamentsspiegel.upload vsberichte.upload

# all the things
all: pull mmmeta push

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

test.states: test.bw test.by test.hh test.mv test.st test.th

test.parldok: test.hh test.mv test.th

test.starweb: test.st

test.%:
	rm -rf testdata
	mkdir testdata
	pytest -s --cov=dokukratie --cov-report term-missing ./tests/ -k "test_$*"
	rm -rf testdata


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
