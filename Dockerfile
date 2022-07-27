FROM python:latest

RUN apt-get update
RUN apt-get install net-tools
RUN pip install ecdsa numba requests

ADD . .
RUN python3 install_decint.py

CMD ifconfig
CMD python3 boot.py