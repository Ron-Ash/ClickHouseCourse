# ClickHouse Course

ClickHouse = **Click**stream data ware**House**, is a column-oriented Database Management System (DBMS) used for Online Analytical Processing (OLAP) focusing on providing fast response to complex analysis on massive amounts of data ("can easily be 1,000x faster than row-oriented DBMS when used in OLAP scenarios").

Base ClickHouse data types:
![alt text](image.png)
Note that ANSI SQL data types all have appropriate aliases

- ClickHouse can also read and write in dozens of formats (https://clickhouse.com/docs/en/interfaces/formats)

Running on own machine: (using Docker)

- `docker run -d --name some-clickhouse-server --ulimit nofile=262144:262144 clickhouse` starts the ClickHouse server
- `docker exec -it some-clickhouse-server clickhouse-client` enters the user to the built-in ClickHouse client CLI

## Architecture

ClickHouse has a lot of different ways to retrieve and store data to optimize storage and access. Each table has an **_Engine_** (https://clickhouse.com/docs/en/engines/table-engines) which determines how and where its data is stored (local file system, in-memory, external systems, materialized views, ...), defined using `ENGINE = <engine_name>` in the `CREATE TABLE` query.

- It also defines which queries are supported, concurrent data access, multithreading request capabilities, replication, and more.
- There are many _engines_ to integrate ClickHouse with external systems.

#### _Special Engines_:

![alt text](image-8.png)

Almost always the **_MergeTree_** table _engine_ (or one of the other _engines_ in the _MergeTree_ family) will be used as they are the most universal and functional table _engines_ for high-load tasks.

```sql
CREATE TABLE my_db.my_table
(
    column1     FixedString(1),
    column2     UInt32,
    column3     String
)
ENGINE = MergeTree
ORDER BY (column1, column2)
```

Primary key determines how the data is stored and searched, if no `PRIMARY KEY` is specifically defined, then it uses the `ORDER BY` clause. Primary Keys in ClickHouse are not (necessarily) unique to each row (pick columns tha are most frequently searched on). The best strategy is "**lower cardinality values early in the primary key**" (will allows ClickHouse to skip more _granules_ that are straight away not desired)

`INSERT`s are performed in bulk, creating a **_part_** (stored in its own folder). Each column in a _part_ has an immutable file with just the column's data:
![alt text](image-1.png)

|                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |                          |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| The `primary.idx` file consists of a key per **_granule_** (single, large chunk of rows). So by default, each key represents at most 8,912 rows (or 10MB) of data. This sparse behavior allows for the key to be stored (lives/) in memory (can have millions of rows in database but only hundreds of entries in the primary index), with the file acting as a backup (is not read to be used, only read to be loaded into memory). The **Primary Index** is the value of the primary key of the first row in a _granule_. | ![alt text](image-5.png) |

**Granule is the smallest indivisible data set that ClickHouse reads when searching rows**.
![alt text](image-6.png)
Once ClickHouse knows the _granule(s)_ (called a **_stripe of granules_**) that need to be serached, each _stripe of granules_ is sent to a thread for processing (_stripes_ are processed concurrently, with faster threads stealing tasks from slower threads).

ClickHouse then merges these created folders (partly why its called a _MergeTree_) over time; deleting the unused, redundant _parts_ in favour of the coalesced _merged part_. This process it then continued on the _merged part_ folders, creating a cascading tree of merges (Note that this will not end in a single folder as there is a size limit enforced).
![alt text](image-2.png)
![alt text](image-3.png)
![alt text](image-4.png)

## Modeling Data

As in most DBMSs, ClickHouse logically groups tables into **_databases_** (`CREATE DATABASE my_database`), with the predifined databases being defined at server initialisation: (required for ClickHouse managment processes)
![alt text](image-7.png)
Note that databases also have _engines_; with the default _database engine_ being **_Atomic_**, unless using **_ClickHouse Cloud_** in which case the default _database engine_ is **_Replicated_**.

Table creation also follows traditional DBMSs with teh exception of the _engine_:
![alt text](image-9.png)

Aside from all the expected SQL-like data types that ClickHouse provides, it additionally provides some more unique and interesting types like:

- **_Array(T)_** defines an array where all the elements have the same data type
  | | |
  | - | - |
  | ![alt text](image-10.png) | ![alt text](image-11.png) define array using `[]` or `array()` |

- **_Nullable(T)_** allows for NULL values to be used for missing values (if it is not important to the buisness logic, do not use as it increases dimentionality of table)
  | | |
  | - | - |
  | ![alt text](image-12.png) | ![alt text](image-13.png) |

- **_Enum(T)_** is used for defining enumerations
  | | |
  | - | - |
  | ![alt text](image-14.png) | _enum_ column can only contain values in its definition, else throws exception ![alt text](image-15.png) |

  ![alt text](image-16.png)

- **_LowCardinality(T)_** is useful when a column has a relatively small number of unique values (hard to quantify but can be useful with **<=10000 unique values**); as it uses **dictionary encoding** to store the values as integers. Advantage over _enum()_ as new values can be dynamically added (no need to know all unique values at creation time).
  ![alt text](image-17.png)

Primary keys can be defined in several ways:

- **Inside** column list:
  ![alt text](image-18.png)
- **Outside** column list:
  ![alt text](image-19.png)
- Using `ORDER BY` instead of `PRIMARY KEY` (with no `PRIMARY KEY` clause)
  ![alt text](image-20.png)

iF both `ORDER BY` and `PRIMARY KEY` are defined, the **primary key** must be a **prefix of** the **order by tuple**:
![alt text](image-21.png)

![alt text](image-22.png)
Good candidates for primary key columns are ones which are queried on frequently, ordered by cardinality in ascending order (at some point adding a column to a primary key no longer provides any benefit).

For creating additional primary indexes consider:

- creating two tables for the same data with different primary keys.
- use **_projection_** (ClickHouse creates hidden table that stores the data sorted in a different way)
- use a **_materialized view_**, a seperate tables based on a SELECT statement.
- define a **_skipping index_**

It's logical to assume that partitioning (logical combination of records in a table by a specific criterion) data improves query performance and they can help limit the number of granules serached but partitions (in ClickHouse) are mostly for data managment.
![alt text](image-23.png)
Partitions can improved the performance of mutations, moving data around, retention policies, adn so on. In general, to improve performance focu on defining a good primary key.

In most cases, partition key is not required; and in most other cases, a partition key more granular than by month is not required.

## Inserting Data

![alt text](image-24.png)
sometimes ClickHouse can infer the column names and data types (schema might not have to be defined explicitly). And sometimes ClickHouse can also figure out the format of the datafile (from the filename extension); and its compression (from its extension)

ClickHouse supports over 75 data formats (TSV, CSV, ..., 20+ formats for JSON data, ..., Protobuf, Parquet, Arrow, ...)

**_Table Engine_** has to be used for Provider-Subscriber platforms like Kafka (uses ClickPipes if using ClickHouse Cloud)
![alt text](image-25.png)

### Table Functions vs Table Engines

![alt text](image-26.png)
table engines in general store all the connection details, teh type of file, the schema, the credentials, etc. These are not required to be entered everytime they are accessed (like a proxy) instead the files stay on the 3rd party server but can be queried as if on the ClickHouse server (when queried streams data to ClickHouse server).
| | |
|-|-|
|![alt text](image-27.png)|![alt text](image-28.png)|

PostgreSQL and MySQL have special **_database engines_** as well:
![alt text](image-29.png)

## Materialized Views

The concept of views in ClickHouse is similar to views in other DBMSs; with the contents of a view table being based on teh results of a `SELECT` query.
![alt text](image-30.png)

### Parameterized Views

ClickHouse additionally facilitates **_Parameterized Views_**, allowing for the view definition to change based on some parameters that can be fed at query execution time.

```sql
CREATE VIEW raw_data_parametrized AS
SELECT *
FROM raw_data
WHERE (id >= {id_from:UInt32}) AND (id <= {id_to:UInt32});
```

```sql
clickhouse-cloud :) SELECT count() FROM raw_data_parametrized(id_from=0, id_to=50000);

SELECT count()
FROM raw_data_parametrized(id_from = 0, id_to = 50000)

Query id: 5731aae1-3e68-4e63-b57f-d50f29055744

┌─count()─┐
│ 317019  │
└─────────┘

1 row in set. Elapsed: 0.004 sec. Processed 319.49 thousand rows, 319.49 KB (76.29 million rows/s., 76.29 MB/s.)
```

Materialized Views in ClickHouse are `INSERT` triggers that **store** the result of a query inside anothe rdestination table. This means that when an `INSERT` happens to the source table of the `SELECT` query, the query is executed on newly-inserted rows and the result is inserted into the MV table (No trigger on `DELETE`, `UPDATE`,etc.).
![alt text](image-31.png)
Note that ClickHouse creates a hidden table in addition to the materialized view for each MV, called `.inner.{uuid}` (has to do with how MVs work in ClickHouse). Instead of having ClickHouse implicitly create `.inner.{uuid}` as the hidden table; one can define an explicit table for a view, and then define a materialized view that sends its data **_"to"_** the explicit table (seperate the view from its underlying table):

1. Define the **_destination table_**

   ```sql
   CREATE TABLE uk_price_by_town_dest (
     price UInt32,
     date  Date,
     streat  LowCardinality(String),
     town  LowCardinality(String),
     district  LowCardinality(String)
   )
   ENGINE = MergeTree
   ORDER BY town;
   ```

2. Define the MV using the `TO` clause "to: the destination table

   ```sql
   CREATE MATERIALIZED VIEW uk_price_by_town_view TO uk_price_by_town_dest AS (
     SELECT price, date, street, town, district FROM uk_price_paid
     WHERE date >= toDate('2024-02-19 12:30:00')
   );

   ```

3. **_Populate the destination_** table with historic data

   ```sql
   INSERT INTO uk_price_by_town_dest
     SELECT price, date, street, town, district FROM uk_price_paid
     WHERE date < toDate('2024-02-19 12:30:00')
   ```
