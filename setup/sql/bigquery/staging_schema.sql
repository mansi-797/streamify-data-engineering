-- Streamify BigQuery staging schema
-- Cloud-ready definition only.
-- This file is not executed against a live BigQuery project locally.

CREATE TABLE IF NOT EXISTS `streamify_stg.listen_events` (
    artist STRING,
    song STRING,
    duration FLOAT64,
    ts TIMESTAMP,
    auth STRING,
    level STRING,
    city STRING,
    state STRING,
    useragent STRING,
    lon FLOAT64,
    lat FLOAT64,
    userid INT64,
    lastname STRING,
    firstname STRING,
    gender STRING,
    registration INT64
);

CREATE TABLE IF NOT EXISTS `streamify_stg.page_view_events` (
    ts TIMESTAMP,
    page STRING,
    auth STRING,
    method STRING,
    status INT64,
    level STRING,
    city STRING,
    state STRING,
    useragent STRING,
    lon FLOAT64,
    lat FLOAT64,
    userid INT64,
    lastname STRING,
    firstname STRING,
    gender STRING,
    registration INT64,
    artist STRING,
    song STRING,
    duration FLOAT64
);

CREATE TABLE IF NOT EXISTS `streamify_stg.auth_events` (
    ts TIMESTAMP NOT NULL,
    sessionid INT64 NOT NULL,
    level STRING,
    city STRING,
    state STRING,
    useragent STRING,
    lon FLOAT64,
    lat FLOAT64,
    userid INT64,
    lastname STRING,
    firstname STRING,
    gender STRING,
    registration INT64,
    success BOOL NOT NULL
);
