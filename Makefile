START ?= 20220601
END ?= 20220630
INST ?= "University+of+Texas"
USERLIST ?= "utrc_report_2022-06-01_to_2022-07-01.xlsx"
OUTPUT ?= "output_jun_2022.xlsx"

VER ?= 0.1
APP ?= "wjallen/funding-scraper"
UID := $(shell id -u)
GID := $(shell id -g)


build:
	docker build -t ${APP}:${VER} .

run: build
	touch ./data/${OUTPUT} ./data/DOE_${OUTPUT}
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /nsf_api_scraper.py \
                   --start ${START} --end ${END} --inst ${INST} --userlist ${USERLIST} --output ${OUTPUT}
	docker run --rm -v ${PWD}/data:/data -u ${UID}:${GID} ${APP}:${VER} python /doe_scraper.py \
                   --start ${START} --end ${END} --userlist ${USERLIST} --output ${OUTPUT}
				   
int: build
	docker run --rm -it ${APP}:${VER} python

push:
	docker push ${APP}:${VER}

