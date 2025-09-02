FROM --platform=amd64 python:3.10-slim AS source

# make sure image can run as non-root user


ENV POETRY_CACHE_DIR=/poetry/.cache
ENV POETRY_CONFIG_DIR=/poetry/.config
ENV POETRY_HOME=/poetry

RUN pip install poetry
COPY . /src
WORKDIR /src

RUN poetry install
RUN poetry build --format=wheel

RUN chmod og+rwX /poetry
RUN chmod og+rwX -R /src



FROM --platform=amd64 ubuntu:22.04 AS run

RUN DEBIAN_FRONTEND="noninteractive" apt-get update && apt-get -y install tzdata
RUN apt-get install -y python3.10 curl
RUN curl -ksS https://bootstrap.pypa.io/get-pip.py | python3.10

COPY --from=source /src/dist /dist
RUN pip install /dist/*.whl
