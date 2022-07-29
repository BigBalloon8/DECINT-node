FROM python:latest

RUN apt-get update
RUN apt-get install net-tools
RUN pip install ecdsa numba requests


ADD . .
RUN pip install --editable .

