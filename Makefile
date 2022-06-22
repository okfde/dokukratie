export MEMORIOUS_CONFIG_PATH=dokukratie
export MEMORIOUS_USER_AGENT="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"

# production use: `make <crawler>`
# current available scrapers:
# state scrapers
bb: bb.pull bb.run_prod bb.mmmeta bb.upload
be: be.pull be.run_prod be.mmmeta be.upload
bw: bw.pull bw.run_prod bw.mmmeta bw.upload
by: by.pull by.run_prod by.mmmeta by.upload
hb: hb.pull hb.run_prod hb.mmmeta hb.upload
hh: hh.pull hh.run_prod hh.mmmeta hh.upload
he: he.pull he.run_prod he.mmmeta he.upload
mv: mv.pull mv.run_prod mv.mmmeta mv.upload
ni: ni.pull ni.run_prod ni.mmmeta ni.upload
nw: nw.pull nw.run_prod nw.mmmeta nw.upload
rp: rp.pull rp.run_prod rp.mmmeta rp.upload
sh: sh.pull sh.run_prod sh.mmmeta sh.upload
sl: sl.pull sl.run_prod sl.mmmeta sl.upload
sn: sn.pull sn.run_prod sn.mmmeta sn.upload
st: st.pull st.run_prod st.mmmeta st.upload
th: th.pull th.run_prod th.mmmeta th.upload

# other scrapers
dip: dip.pull dip.run_prod dip.mmmeta dip.upload
parlamentsspiegel: parlamentsspiegel.pull parlamentsspiegel.run_prod parlamentsspiegel.mmmeta parlamentsspiegel.upload
sehrgutachten: sehrgutachten.pull sehrgutachten.run_prod sehrgutachten.mmmeta sehrgutachten.upload
vsberichte: vsberichte.pull vsberichte.run_prod vsberichte.mmmeta vsberichte.upload

# all the things
config.states: bb.config bw.config by.config hh.config he.config mv.config ni.config nw.config rp.config st.config th.config
action.states: bb.action bw.action by.action hh.action he.action mv.action ni.action nw.action rp.action st.action th.action
pull.states: bb.pull bw.pull by.pull hh.pull he.pull mv.pull ni.pull nw.pull rp.pull st.pull th.pull
mmmeta.states: bb.mmmeta bw.mmmeta by.mmmeta hh.mmmeta he.mmmeta mv.mmmeta ni.mmmeta nw.mmmeta rp.mmmeta st.mmmeta th.mmmeta
upload.states: bb.upload bw.upload by.upload hh.upload he.upload mv.upload ni.upload nw.upload rp.upload st.upload th.upload
push.states: bb.push bw.push by.push hh.push he.push mv.push ni.push nw.push rp.push st.push th.push
download.states: bb.download bw.download by.download hh.download he.download mv.download ni.download nw.download rp.download st.download th.download
download.states: bb.download bw.download by.download hh.download he.download mv.download ni.download nw.download rp.download st.download th.download
sync.states: states.config states.pull states.mmmeta states.upload

config: config.states dip.config sehrgutachten.config
pull: pull.states dip.pull sehrgutachten.pull
sync: sync.states dip.sync sehrgutachten.sync
push: push.states dip.push sehrgutachten.push
download: download.states dip.download sehrgutachten.download

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
	aws --endpoint-url $(ARCHIVE_ENDPOINT_URL) s3 sync s3://$(DATA_BUCKET)/$*/_mmmeta/db/ ./data/store/$*/_mmmeta/db

%.push:
	aws --endpoint-url $(ARCHIVE_ENDPOINT_URL) s3 sync --exclude "*.db*" ./data/store/$*/_mmmeta/ s3://$(DATA_BUCKET)/$*/_mmmeta

%.upload:
	aws --endpoint-url $(ARCHIVE_ENDPOINT_URL) s3 sync --exclude "*.db*" ./data/store/$*/ s3://$(DATA_BUCKET)/$*

%.download:
	aws --endpoint-url $(ARCHIVE_ENDPOINT_URL) s3 sync s3://$(DATA_BUCKET)/$* ./data/store/$*

test: install.test
	rm -rf testdata
	mkdir testdata
	pytest -s --cov=dokukratie --cov-report term-missing ./tests/
	rm -rf testdata

test.%:
	rm -rf testdata/$*
	mkdir -p testdata/$*
	pytest -s --cov=dokukratie --cov=memorious_extended --cov-report term-missing ./tests/ -k "test_$*"
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
