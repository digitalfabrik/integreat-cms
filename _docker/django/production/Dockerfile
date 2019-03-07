FROM ubuntu

RUN echo $PWD
RUN who

RUN apt-add-repository ...
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install --yes --force-yes integreat-cms

# remove deprecated pycrypto package
RUN DEBIAN_FRONTEND=noninteractive apt remove --yes --force-yes python3-crypto

EXPOSE 8000
