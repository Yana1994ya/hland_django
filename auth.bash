#!/usr/bin/env bash

set -Eeuo pipefail
trap cleanup SIGINT SIGTERM ERR EXIT

cleanup() {
  trap - SIGINT SIGTERM ERR EXIT
  # script cleanup here
  rm /tmp/acme_$CERTBOT_TOKEN
}

echo $CERTBOT_VALIDATION > /tmp/acme_$CERTBOT_TOKEN

aws \
  --profile private \
  s3 \
  cp \
  /tmp/acme_$CERTBOT_TOKEN \
  s3://hland-assets/.well-known/acme-challenge/$CERTBOT_TOKEN \
  --acl public-read
