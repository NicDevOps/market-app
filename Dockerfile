FROM python:3.8-slim-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "flask" ]

CMD [ "run", "--host=0.0.0.0" ]