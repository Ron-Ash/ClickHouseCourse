-- create uk_price_paid using the documentation below:
-- https://clickhouse.com/docs/en/getting-started/example-datasets/uk-price-paid

CREATE TABLE uk_prices_aggs_dest
(
    `month` Date,
    `min_price` SimpleAggregateFunction(min, UInt32),
    `max_price` SimpleAggregateFunction(max, UInt32),
    `avg_price` AggregateFunction(avg, UInt32),
    `volume` AggregateFunction(count, UInt32)
)
ENGINE = AggregatingMergeTree
ORDER BY month
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW uk_prices_aggs_view TO uk_prices_aggs_dest
AS SELECT
    toStartOfMonth(date) AS month,
    minSimpleState(price) AS min_price,
    maxSimpleState(price) AS max_price,
    avgState(price) AS avg_price,
    countState(price) AS volume
FROM uk_price_paid
GROUP BY month;

INSERT INTO uk_prices_aggs_dest SELECT
    toStartOfMonth(date) AS month,
    minSimpleState(price) AS min_price,
    maxSimpleState(price) AS max_price,
    avgState(price) AS avg_price,
    countState(price) AS volume
FROM uk_price_paid
GROUP BY month;

SELECT 
    month,
    countMerge(volume),
    min(min_price),
    max(max_price)
FROM uk_prices_aggs_dest
WHERE toYYYYMM(month) = '202408'
GROUP BY month;


INSERT INTO uk_price_paid (date, price, town) VALUES
    ('2024-08-01', 30000000, 'Little Whinging'),
    ('2024-08-01', 1, 'Little Whinging');