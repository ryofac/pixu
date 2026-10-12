#!/usr/bin/env bash

set -euo pipefail

django_image="${PIXU_DJANGO_IMAGE:-pixu_django:production}"
postgres_image="${PIXU_POSTGRES_IMAGE:-pixu_postgres:production}"
nginx_image="${PIXU_NGINX_IMAGE:-pixu_nginx:production}"
traefik_image="${PIXU_TRAEFIK_IMAGE:-pixu_traefik:production}"
redis_image="${PIXU_REDIS_IMAGE:-redis:7.2}"
images_bundle="${PIXU_VM_IMAGES_BUNDLE:-pixu-vm-images.tar.gz}"
target_platform="${1:-}"

if [[ -n "${target_platform}" && "${target_platform}" != "linux/amd64" && "${target_platform}" != "linux/arm64" ]]; then
  printf 'Plataforma inválida: %s (use linux/amd64 ou linux/arm64).\n' "${target_platform}" >&2
  exit 2
fi

build_image() {
  local dockerfile="$1"
  local image="$2"

  if [[ -n "${target_platform}" ]]; then
    docker buildx build --platform "${target_platform}" --load -f "${dockerfile}" -t "${image}" .
  else
    docker build -f "${dockerfile}" -t "${image}" .
  fi
}

native_platform="$(docker info --format '{{.OSType}}/{{.Architecture}}')"
case "${native_platform}" in
  linux/x86_64|linux/amd64) native_platform=linux/amd64 ;;
  linux/aarch64|linux/arm64) native_platform=linux/arm64 ;;
esac
bundle_platform="${target_platform:-${native_platform}}"
if [[ "${bundle_platform}" != "linux/amd64" && "${bundle_platform}" != "linux/arm64" ]]; then
  printf 'Arquitetura local não suportada para o bundle: %s.\n' "${bundle_platform}" >&2
  exit 2
fi
commit_sha="$(git rev-parse --verify HEAD)"

npm ci
npm run build

build_image compose/production/django/Dockerfile "${django_image}"
build_image compose/production/postgres/Dockerfile "${postgres_image}"
build_image compose/production/nginx/Dockerfile "${nginx_image}"
build_image compose/production/traefik/vm.Dockerfile "${traefik_image}"
if [[ -n "${target_platform}" ]]; then
  docker pull --platform "${target_platform}" "${redis_image}"
else
  docker pull "${redis_image}"
fi

bundle_dir="$(dirname "${images_bundle}")"
bundle_name="$(basename "${images_bundle}")"
mkdir -p "${bundle_dir}"
bundle_stage="$(mktemp -d "${bundle_dir}/.pixu-vm-images.XXXXXX")"
trap 'rm -rf "${bundle_stage}"' EXIT
docker save -o "${bundle_stage}/images.tar" "${django_image}" "${postgres_image}" "${nginx_image}" "${traefik_image}" "${redis_image}"
{
  printf 'commit=%s\n' "${commit_sha}"
  printf 'platform=%s\n' "${bundle_platform}"
} > "${bundle_stage}/metadata.txt"
tar -czf "${images_bundle}" -C "${bundle_stage}" images.tar metadata.txt
(cd "${bundle_dir}" && sha256sum "${bundle_name}" > "${bundle_name}.sha256")

printf 'Imagens prontas para a VM:\n'
printf '  %s\n' "${django_image}" "${postgres_image}" "${nginx_image}" "${traefik_image}" "${redis_image}"
printf 'Plataforma: %s\n' "${bundle_platform}"
printf 'Bundle gerado: %s\n' "${images_bundle}"
printf 'Checksum: %s\n' "${bundle_dir}/${bundle_name}.sha256"
