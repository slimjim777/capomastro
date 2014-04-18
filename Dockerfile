FROM schwuk/python2.7
MAINTAINER David Murphy <dave@schwuk.com>

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libpq-dev

ADD . /capomastro

WORKDIR /capomastro

RUN pip install -r requirements.txt

ENTRYPOINT ["./manage.py"]

CMD ["help"]

EXPOSE 8000
