# Dockerfile for ClickHouse database host
FROM clickhouse:24

WORKDIR /

ARG path

COPY ${path}/* ./etc/clickhouse-server/config.d/

# docker build -f ./Dockerfile_chnode --build-arg path=./chnode1 -t chnode1 .