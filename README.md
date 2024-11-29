# ClickHouse Course

ClickHouse = **Click**stream data ware**House**, is a column-oriented Database Management System (DBMS) used for Online Analytical Processing (OLAP) focusing on providing fast response to complex analysis on massive amounts of data ("can easily be 1,000x faster than row-oriented DBMS when used in OLAP scenarios").

Base ClickHouse data types:
![alt text](image.png)
Note that ANSI SQL data types all have appropriate aliases

- ClickHouse can also read and write in dozens of formats (https://clickhouse.com/docs/en/interfaces/formats)

Running on own machine: (using Docker)

- `docker run -d --name some-clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-serve` starts the ClickHouse server
- `docker exec -it some-clickhouse-server clickhouse-client` enters the user to the built-in ClickHouse client CLI

## Architecture

ClickHouse
