FROM ubuntu

COPY ./backend/ /var/www/backend
RUN echo $PWD
WORKDIR /var/www/backend
RUN who

RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install --yes --force-yes python3 python3-pip

# remove deprecated pycrypto package
RUN DEBIAN_FRONTEND=noninteractive apt remove --yes --force-yes python3-crypto

RUN pip3 install -r requirements.txt

EXPOSE 8000
