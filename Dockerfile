FROM python:3.9.13-alpine3.16

ADD ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt && \
    rm /requirements.txt

ADD ./src/nih_api_scraper.py /nih_api_scraper.py
RUN chmod go=u-w /nih_api_scraper.py

CMD ["python", "/nih_api_scraper.py", "-h"]

