FROM ubuntu:14.04
MAINTAINER David Murphy <dave@schwuk.com>

# Add and update sources
RUN echo "deb http://archive.ubuntu.com/ubuntu/ trusty main restricted universe" > /etc/apt/sources.list && \
    echo "deb http://archive.ubuntu.com/ubuntu/ trusty-updates main restricted universe" >> /etc/apt/sources.list && \
    apt-get update

# Install dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python \
    python-dev \
    build-essential \
    python-pip \
    libpq-dev


ADD . /opt/capomastro

WORKDIR /opt/capomastro

RUN pip install -r requirements.txt

ENTRYPOINT ["./manage.py"]

CMD ["help"]
