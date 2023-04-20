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
de_vsberichte: de_vsberichte.pull de_vsberichte.run_prod de_vsberichte.mmmeta de_vsberichte.upload

# all the things
config.states: bb.config be.config bw.config by.config hb.config hh.config he.config mv.config ni.config nw.config rp.config sh.config sl.config sn.config st.config th.config
action.states: bb.action be.action bw.action by.action hb.action hh.action he.action mv.action ni.action nw.action rp.action sh.action sl.action sn.action st.action th.action
pull.states: bb.pull be.pull bw.pull by.pull hb.pull hh.pull he.pull mv.pull ni.pull nw.pull rp.pull sh.pull sl.pull sn.pull st.pull th.pull
mmmeta.states: bb.mmmeta be.mmmeta bw.mmmeta by.mmmeta hb.mmmeta hh.mmmeta he.mmmeta mv.mmmeta ni.mmmeta nw.mmmeta rp.mmmeta sh.mmmeta sl.mmmeta sn.mmmeta st.mmmeta th.mmmeta
upload.states: bb.upload be.upload bw.upload by.upload hb.upload hh.upload he.upload mv.upload ni.upload nw.upload rp.upload sh.upload sl.upload sn.upload st.upload th.upload
push.states: bb.push be.push bw.push by.push hb.push hh.push he.push mv.push ni.push nw.push rp.push sh.push sl.push sn.push st.push th.push
download.states: bb.download be.download bw.download by.download hb.download hh.download he.download mv.download ni.download nw.download rp.download sh.download sl.download sn.download st.download th.download
sync.states: bb.sync be.sync bw.sync by.sync hb.sync hh.sync he.sync mv.sync ni.sync nw.sync rp.sync sh.sync sl.sync sn.sync st.sync th.sync

config: config.states dip.config sehrgutachten.config
pull: pull.states dip.pull sehrgutachten.pull
sync: sync.states dip.sync sehrgutachten.sync
push: push.states dip.push sehrgutachten.push
download: download.states dip.download sehrgutachten.download

he.run_prod:
	# don't ddos hessen
	MEMORIOUS_HTTP_RATE_LIMIT=30 MMMETA=./data/store/he memorious run he
	sqlite3 data/store/he/memorious.db "DELETE FROM memorious_tags WHERE value = '\"\"'"
	sqlite3 data/store/he/memorious.db "VACUUM"

parlamentsspiegel.run_prod:
	# don't go back too far
	START_DATE_DELTA=2 MMMETA=./data/store/parlamentsspiegel memorious run parlamentsspiegel

de_vsberichte.run_prod:
	# don't use mmmeta
	MEMORIOUS_DATASTORE_URI=sqlite:///data/store/de_vsberichte/memorious.db memorious run de_vsberichte


%.run_prod:
	MEMORIOUS_DATASTORE_URI=sqlite:///data/store/$*/memorious.db MMMETA=./data/store/$* memorious run $*
	# cleanup tags table
	sqlite3 data/store/$*/memorious.db "DELETE FROM memorious_tags WHERE value = '\"\"'"
	sqlite3 data/store/$*/memorious.db "VACUUM"

run.%:
	memorious run $*

install:
	pip install -e .

install.dev: install
	pip install -r requirements-dev.txt

install.prod: install
	pip install -r requirements-prod.txt

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
	aws --endpoint-url $(ARCHIVE_ENDPOINT_URL) s3 cp s3://$(DATA_BUCKET)/$*/memorious.db ./data/store/$*/memorious.db

%.push:
	aws --endpoint-url $(ARCHIVE_ENDPOINT_URL) s3 sync --exclude "*state.db*" ./data/store/$*/_mmmeta/ s3://$(DATA_BUCKET)/$*/_mmmeta

%.upload:
	aws --endpoint-url $(ARCHIVE_ENDPOINT_URL) s3 sync --exclude "*state.db*" ./data/store/$*/ s3://$(DATA_BUCKET)/$*

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

catalog:
	python common/catalog.py
	aws s3 --endpoint-url https://s3.investigativedata.org cp --no-progress --cache-control "public, max-age=3600" --metadata-directive REPLACE --acl public-read catalog.json s3://dokukratie/catalog.json
