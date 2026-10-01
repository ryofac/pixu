#!/usr/bin/env bash

set -euo pipefail

django_image="${PIXU_DJANGO_IMAGE:-pixu_django:production}"
postgres_image="${PIXU_POSTGRES_IMAGE:-pixu_postgres:production}"
nginx_image="${PIXU_NGINX_IMAGE:-pixu_nginx:production}"
traefik_image="${PIXU_TRAEFIK_IMAGE:-pixu_traefik:production}"
redis_image="${PIXU_REDIS_IMAGE:-redis:7.2}"
images_bundle="${PIXU_VM_IMAGES_BUNDLE:-pixu-vm-images.tar.gz}"

npm ci
npm run build

docker build -f compose/production/django/Dockerfile -t "${django_image}" .
docker build -f compose/production/postgres/Dockerfile -t "${postgres_image}" .
docker build -f compose/production/nginx/Dockerfile -t "${nginx_image}" .
docker build -f compose/production/traefik/vm.Dockerfile -t "${traefik_image}" .
docker pull "${redis_image}"

bundle_dir="$(dirname "${images_bundle}")"
mkdir -p "${bundle_dir}"
docker save "${django_image}" "${postgres_image}" "${nginx_image}" "${traefik_image}" "${redis_image}" \
  | gzip > "${images_bundle}"

printf 'Imagens prontas para a VM:\n'
printf '  %s\n' "${django_image}" "${postgres_image}" "${nginx_image}" "${traefik_image}" "${redis_image}"
printf 'Bundle gerado: %s\n' "${images_bundle}"
