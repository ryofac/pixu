#!/usr/bin/env bash

set -euo pipefail

vm_ip="${1:-${PIXU_VM_IP:-}}"
output_dir="${2:-deploy/vm/tls}"

if [[ -z "${vm_ip}" ]]; then
  printf 'Uso: %s <ip-da-vm> [diretorio-de-saida]\n' "$0" >&2
  exit 64
fi

mkdir -p "${output_dir}"
umask 077

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "${output_dir}/pixu.key" \
  -out "${output_dir}/pixu.crt" \
  -sha256 \
  -days 825 \
  -subj "/CN=${vm_ip}" \
  -addext "subjectAltName=IP:${vm_ip}"

printf 'Certificado criado em %s (SAN IP: %s).\n' "${output_dir}" "${vm_ip}"
