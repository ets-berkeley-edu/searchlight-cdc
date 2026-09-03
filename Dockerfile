FROM python:3.13-trixie

ARG PACKAGES
ARG LAYER_NAME

ENV PACKAGES=$PACKAGES
ENV LAYER_NAME=$LAYER_NAME

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    gcc \
    git \
    python3-dev \
    zip \
    && rm -rf /var/lib/apt/lists/*

RUN pip --no-cache-dir --disable-pip-version-check install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir --disable-pip-version-check $PACKAGES -t /app/python

CMD ["/bin/sh", "-c", "zip -r $LAYER_NAME.zip ."]
