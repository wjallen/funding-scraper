FROM python:3.9.13-alpine3.16

ADD ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt && \
    rm /requirements.txt

ADD ./src/* /code/
RUN chmod go=u-w /code/*

CMD ["python", "/nsf_api_scraper.py", "-h"]

