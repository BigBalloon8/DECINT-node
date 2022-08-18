FROM python:latest

RUN apt-get update
RUN python3 -m pip install --upgrade pip
RUN pip install ecdsa numba requests click

ADD . .
RUN pip install --editable .

CMD python

