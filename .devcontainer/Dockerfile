FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

RUN apt-get update && \
    apt-get install -y nodejs npm && \
    npm install -g n && \
    n stable && \
    apt-get purge -y nodejs npm && \
    ln -sf /usr/local/bin/node /usr/bin/node

RUN apt-get install -y netcat-traditional pcregrep

WORKDIR /workspace

CMD ["sleep", "infinity"]
