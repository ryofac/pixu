FROM docker.io/traefik:v3.7.13

LABEL org.opencontainers.image.source="https://github.com/ryofac/pixu"

RUN mkdir -p /etc/traefik/acme \
  && touch /etc/traefik/acme/acme.json \
  && chmod 600 /etc/traefik/acme/acme.json

COPY ./deploy/vm/traefik.yml /etc/traefik/traefik.yml
