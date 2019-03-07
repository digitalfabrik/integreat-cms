FROM ubuntu

COPY ./backend/ /opt/integreat-cms
RUN echo $PWD
WORKDIR /opt/integreat-cms
RUN who

RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install --yes --force-yes python3 python3-pip

# remove deprecated pycrypto package
RUN DEBIAN_FRONTEND=noninteractive apt remove --yes --force-yes python3-crypto

RUN python3 setup.py install

EXPOSE 8000