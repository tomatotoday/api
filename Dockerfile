FROM python:2

ADD . /tmp/app

RUN cd /tmp/app && python setup.py install
RUN pip install gunicorn

EXPOSE 10000

CMD gunicorn -w 8 -b 0.0.0.0:10000 tomato.api.wsgi:app
