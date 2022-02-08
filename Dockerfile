FROM python:3.8-slim-buster

COPY ./requirements.txt /app/requirements.txt

# COPY ./ta-lib-0.4.0-src.tar.gz /app/ta-lib-0.4.0-src.tar.gz

WORKDIR /app

RUN apt-get update && apt-get install -y make wget gcc

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz

RUN mkdir /ta-lib

RUN tar -xf ta-lib-0.4.0-src.tar.gz -C /ta-lib

WORKDIR "/ta-lib/ta-lib"

RUN ./configure --prefix=/usr

RUN make install

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "flask" ]

CMD [ "run", "--host=0.0.0.0" ]