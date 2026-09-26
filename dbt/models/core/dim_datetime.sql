{{ config(materialized = 'table') }}

WITH date_series AS (
    SELECT generate_series(
        TIMESTAMP '2018-10-01 00:00:00',
        TIMESTAMP '2027-01-01 00:00:00',
        INTERVAL '1 hour'
    ) AS date
)

SELECT
    EXTRACT(EPOCH FROM date)::BIGINT AS dateKey,
    date,
    EXTRACT(ISODOW FROM date)::INTEGER AS dayOfWeek,
    EXTRACT(DAY FROM date)::INTEGER AS dayOfMonth,
    EXTRACT(WEEK FROM date)::INTEGER AS weekOfYear,
    EXTRACT(MONTH FROM date)::INTEGER AS month,
    EXTRACT(YEAR FROM date)::INTEGER AS year,
    CASE
        WHEN EXTRACT(ISODOW FROM date) IN (6, 7) THEN TRUE
        ELSE FALSE
    END AS weekendFlag
FROM date_series
