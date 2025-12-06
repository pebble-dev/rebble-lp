FROM python:3.6-alpine
RUN apk add --update build-base libffi-dev zlib-dev
RUN apk add --update postgresql-dev
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
ENV FLASK_ENV=development
CMD flask run -h $HOST
