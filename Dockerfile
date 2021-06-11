FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qq -y update
RUN apt-get install -y -qq python3-pip python3-icu git curl unzip libpq-dev
RUN pip3 install -q pyicu
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
COPY . /opt/memorious
RUN pip3 install -q -e /opt/memorious
RUN pip3 install -r /opt/memorious/requirements-prod.txt
WORKDIR /opt/memorious
