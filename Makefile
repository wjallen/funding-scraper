START ?= 20220901
END ?= 20220930
INST ?= "University+of+Texas"
USERLIST ?= "utrc_report_2023-01-01_to_2023-02-01.xlsx"
OUTPUT ?= "test.xlsx"

APP ?= "wjallen/funding-scraper"
VER ?= 0.2
UID := $(shell id -u)
GID := $(shell id -g)


build:
	docker build -t ${APP}:${VER} .

run: build
#	touch ./data/${OUTPUT} ./data/DOE_${OUTPUT} --Austin: Not seeing the old error with permissions, even with this commented out
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /code/nsf_api_scraper.py \
                     --start ${START} --end ${END} --inst ${INST} --userlist ${USERLIST} --output ${OUTPUT}
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /code/nih_api_scraper.py \
                   --start ${START} --end ${END} --inst ${INST} --userlist ${USERLIST} --output ${OUTPUT}
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /code/doe_scraper.py \
                   --start ${START} --end ${END} --userlist ${USERLIST} --output ${OUTPUT}

int: build
	docker run --rm -it ${APP}:${VER} python

push:
	docker push ${APP}:${VER}

