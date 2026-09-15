FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

RUN rm -f /etc/apt/sources.list.d/yarn.list
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    npm install -g n && \
    n stable && \
    apt-get purge -y nodejs npm && \
    ln -sf /usr/local/bin/node /usr/bin/node

RUN apt-get install -y netcat-traditional pcregrep libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b
RUN apt-get install -y redis-server && \
    usermod -aG redis www-data

WORKDIR /workspace

CMD ["sleep", "infinity"]
