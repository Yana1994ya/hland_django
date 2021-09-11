#!/usr/bin/env bash

set -Eeuo pipefail

aws \
  --profile private \
  s3 \
  rm \
  s3://hland-assets/.well-known/acme-challenge/$CERTBOT_TOKEN
