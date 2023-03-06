START ?= 20220101
END ?= 20220701
INST ?= "University+of+Texas"
USERLIST ?= "utrc_report_2023-01-01_to_2023-02-01.xlsx"
OUTPUT ?= "test.xlsx"

VER ?= 0.1
APP ?= "joshuaamedina2000/funding-scraper"
UID := $(shell id -u)
GID := $(shell id -g)


build:
	docker build -t ${APP}:${VER} .

run: build
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /nih_api_scraper.py \
                   --start ${START} --end ${END} --inst ${INST} --userlist ${USERLIST} --output ${OUTPUT}

int: build
	docker run --rm -it ${APP}:${VER} python

push:
	docker push ${APP}:${VER}

