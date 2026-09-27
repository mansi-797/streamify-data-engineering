{{ config(materialized='table') }}

WITH base AS (
    SELECT
        userid,
        firstname,
        lastname,
        gender,
        level,
        CAST(registration AS INT64) AS registration,
        DATE(MIN(ts)) AS rowactivationdate,
        DATE '9999-12-31' AS rowexpirationdate,
        1 AS currentrow
    FROM {{ source('staging', 'listen_events') }}
    WHERE userid <> 0
    GROUP BY
        userid,
        firstname,
        lastname,
        gender,
        level,
        registration
)

SELECT
    {{ dbt_utils.surrogate_key(['userid', 'rowactivationdate', 'level']) }} AS userkey,
    *
FROM base
