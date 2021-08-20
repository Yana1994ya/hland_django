#!/usr/bin/env bash

set -Eeuo pipefail

certbot certonly \
  --manual \
  --preferred-challenges http \
  --config-dir certbot/config \
  --work-dir certbot/work \
  --logs-dir certbot/logs \
  --manual \
  --preferred-challenges=http \
  --manual-auth-hook ./auth.bash \
  --manual-cleanup-hook ./auth.cleanup.bash \
  -d hollyland.iywebs.cloudns.ph \
  --force-renewal

aws \
  --profile private \
  acm import-certificate \
  --certificate-arn arn:aws:acm:eu-central-1:620349588955:certificate/7291ae6f-cc76-4f31-98e9-422ba74d1572 \
  --certificate fileb://certbot/config/live/hollyland.iywebs.cloudns.ph/cert.pem \
  --private-key fileb://certbot/config/live/hollyland.iywebs.cloudns.ph/privkey.pem \
  --certificate-chain fileb://certbot/config/live/hollyland.iywebs.cloudns.ph/fullchain.pem