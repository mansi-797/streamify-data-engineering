{{ config(materialized = 'table') }}

WITH date_series AS (
    SELECT date
    FROM UNNEST(
        GENERATE_TIMESTAMP_ARRAY(
            TIMESTAMP('2018-10-01 00:00:00+00'),
            TIMESTAMP('2027-01-01 00:00:00+00'),
            INTERVAL 1 HOUR
        )
    ) AS date
)

SELECT
    UNIX_SECONDS(date) AS dateKey,
    date,
    MOD(EXTRACT(DAYOFWEEK FROM date) + 5, 7) + 1 AS dayOfWeek,
    EXTRACT(DAY FROM date) AS dayOfMonth,
    EXTRACT(ISOWEEK FROM date) AS weekOfYear,
    EXTRACT(MONTH FROM date) AS month,
    EXTRACT(YEAR FROM date) AS year,
    CASE
        WHEN EXTRACT(DAYOFWEEK FROM date) IN (1, 7) THEN TRUE
        ELSE FALSE
    END AS weekendFlag
FROM date_series
