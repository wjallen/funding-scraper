START ?= 20230201
END ?= 20230301
INST ?= "University+of+Texas"
USERLIST ?= "utrc_report_2023-02-01_to_2023-03-01.xlsx"
OUTPUT ?= "output_feb_2023.xlsx"

APP ?= "wjallen/funding-scraper"
VER ?= 0.2
UID := $(shell id -u)
GID := $(shell id -g)


build:
	docker build -t ${APP}:${VER} .

run-nsf: build
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /code/nsf_api_scraper.py \
                     --start ${START} --end ${END} --inst ${INST} --userlist ${USERLIST} --output ${OUTPUT}

run-nih: build
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /code/nih_api_scraper.py \
                   --start ${START} --end ${END} --inst ${INST} --userlist ${USERLIST} --output ${OUTPUT}

run-doe: build
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /code/doe_scraper.py \
                   --start ${START} --end ${END} --userlist ${USERLIST} --output ${OUTPUT}

run-all: run-nsf run-nih run-doe

int: build
	docker run --rm -it ${APP}:${VER} python

push:
	docker push ${APP}:${VER}

