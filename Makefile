export MEMORIOUS_CONFIG_PATH=dokukratie

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
mmmeta: bw.mmmeta by.mmmeta hh.mmmeta mv.mmmeta st.mmmeta th.mmmeta dip.mmmeta sehrgutachten.mmmeta parlamentsspiegel.mmmeta
pull: bw.pull by.pull hh.pull mv.pull st.pull th.pull dip.pull sehrgutachten.pull parlamentsspiegel.pull
push: bw.push by.push hh.push mv.push st.push th.push dip.push sehrgutachten.push parlamentsspiegel.push

# all the things
sync: pull mmmeta push

%.config:
	mkdir -p ./data/store/$*/_mmmeta
	sed "s/<scraper_name>/$*/" config.yml.tmpl > ./data/store/$*/_mmmeta/config.yml

%.mmmeta:
	MMMETA=./data/store/$* mmmeta generate
	# FIXME cleanup
	# rm -rf ./data/store/$*/_mmmeta/*db-*

%.pull:
	aws s3 sync --exclude "*db-shm" --exclude "*db-wal" s3://dokukratie-dev/$*/_mmmeta ./data/store/$*/_mmmeta

%.push:
	aws s3 sync --exclude "*db-shm" --exclude "*db-wal" --exclude "state.db" ./data/store/$*/_mmmeta s3://dokukratie-dev/$*/_mmmeta

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
