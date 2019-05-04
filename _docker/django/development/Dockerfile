FROM ubuntu

COPY ./ /opt/integreat-cms
RUN echo $PWD
WORKDIR /opt/integreat-cms
RUN who

RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install --yes --force-yes python3 python3-pip python3-setuptools libpq-dev python3-venv

# remove deprecated pycrypto package
RUN DEBIAN_FRONTEND=noninteractive apt remove --yes --force-yes python3-crypto

RUN python3 -m venv .venv

RUN echo "source /opt/integreat-cms/.venv/bin/activate" >> /root/.bashrc

EXPOSE 8000