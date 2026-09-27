CREATE TABLE IF NOT EXISTS auth_events (
    ts timestamp without time zone NOT NULL,
    sessionid bigint NOT NULL,
    level text,
    city text,
    state text,
    useragent text,
    lon double precision,
    lat double precision,
    userid bigint,
    lastname text,
    firstname text,
    gender text,
    registration bigint,
    success boolean NOT NULL DEFAULT false,
    CONSTRAINT auth_events_natural_key UNIQUE (ts, sessionid)
);
