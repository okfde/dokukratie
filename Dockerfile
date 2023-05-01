FROM python:3-bullseye

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python3-icu curl unzip

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

RUN pip install -q -U pip setuptools
COPY . /opt/dokukratie
RUN pip3 install -q -e /opt/dokukratie

WORKDIR /opt/dokukratie

ENV ARCHIVE_TYPE=s3
ENV ARCHIVE_BUCKET=memorious
ENV DATA_BUCKET=dokukratie
ENV MEMORIOUS_CONFIG_PATH=dokukratie
ENV MEMORIOUS_EXPIRE=30
ENV MEMORIOUS_HTTP_TIMEOUT=60
ENV MEMORIOUS_CONTINUE_ON_ERROR=1
ENV REDIS_URL=redis://redis:6379/0
ENV AWS_REGION=eu-central-1
ENV AWS_DEFAULT_REGION=eu-central-1
