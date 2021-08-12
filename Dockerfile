FROM python:3.9

RUN pip install poetry

RUN mkdir /root/project
WORKDIR /root/project
COPY poetry.lock ./
COPY pyproject.toml ./

RUN poetry install && \
    poetry env info -p > .virtualenv_path && \
    cp -a `poetry env info -p` .virtualenv


FROM python:3.9

RUN pip install awscli

RUN mkdir /root/project
WORKDIR /root/project

COPY --from=0 /root/project/.virtualenv .virtualenv
COPY --from=0 /root/project/.virtualenv_path .virtualenv_path
COPY hland hland
# Market review doesn't have static files yet, when it does add it here
# so the layer will be effected
RUN mkdir market_review && touch market_review/init.py
COPY manage.py manage.py
COPY deployment/settings_local.dev.py hland/settings_local.py

RUN .virtualenv/bin/python manage.py collectstatic
# Sync the static files with the S3 bucket
RUN --mount=type=secret,id=config,dst=/root/.aws/config \
    --mount=type=secret,id=credentials,dst=/root/.aws/credentials \
    aws s3 sync --acl public-read --cache-control "public, max-age=86400" static s3://hland-assets/static

FROM python:3.9

RUN mkdir /root/project
WORKDIR /root/project

COPY --from=0 /root/project/.virtualenv .virtualenv
COPY --from=0 /root/project/.virtualenv_path .virtualenv_path
COPY hland hland
COPY market_review market_review
COPY manage.py manage.py
COPY templates templates
COPY deployment/settings_local.aws.py hland/settings_local.py
RUN mkdir static
COPY --from=1 /root/project/static/staticfiles.json static/staticfiles.json

RUN mkdir -p `cat .virtualenv_path` && \
    rm -r `cat .virtualenv_path` &&  \
    ln -s /root/project/.virtualenv `cat .virtualenv_path`

EXPOSE 8080
ENTRYPOINT [".virtualenv/bin/gunicorn", \
    "-b", ":8080", \
    "--error-logfile", "-", \
    "--access-logfile", "-", \
    "--log-level", "info", \
    "hland.wsgi"]