import argparse
import os
import io
import csv

import pandas as pd
import pyarrow.dataset as ds
import psycopg2


CONFIG = {
    "listen": {
        "source_path": "streamify_data/listen_events",
        "target_table": "listen_events",
        "source_columns": [
            "artist", "song", "duration", "ts", "auth", "level",
            "city", "state", "userAgent", "lon", "lat", "userId",
            "lastName", "firstName", "gender", "registration"
        ],
        "db_columns": [
            "artist", "song", "duration", "ts", "auth", "level",
            "city", "state", "useragent", "lon", "lat", "userid",
            "lastname", "firstname", "gender", "registration"
        ],
        "defaults": {
            "artist": "NA",
            "song": "NA",
            "duration": -1.0,
            "auth": "NA",
            "level": "NA",
            "city": "NA",
            "state": "NA",
            "useragent": "NA",
            "lon": 0.0,
            "lat": 0.0,
            "userid": 0,
            "lastname": "NA",
            "firstname": "NA",
            "gender": "NA",
            "registration": 9999999999999,
        },
        "key_columns": ["ts", "userid", "artist", "song"],
        "integer_columns": ["userid", "registration"],
    },
    "page": {
        "source_path": "streamify_data/page_view_events",
        "target_table": "page_view_events",
        "source_columns": [
            "ts", "page", "auth", "method", "status", "level",
            "city", "state", "userAgent", "lon", "lat", "userId",
            "lastName", "firstName", "gender", "registration",
            "artist", "song", "duration"
        ],
        "db_columns": [
            "ts", "page", "auth", "method", "status", "level",
            "city", "state", "useragent", "lon", "lat", "userid",
            "lastname", "firstname", "gender", "registration",
            "artist", "song", "duration"
        ],
        "defaults": {
            "page": "NA",
            "auth": "NA",
            "method": "NA",
            "status": 0,
            "level": "NA",
            "city": "NA",
            "state": "NA",
            "useragent": "NA",
            "lon": 0.0,
            "lat": 0.0,
            "userid": 0,
            "lastname": "NA",
            "firstname": "NA",
            "gender": "NA",
            "registration": 9999999999999,
            "artist": "NA",
            "song": "NA",
            "duration": -1.0,
        },
        "key_columns": ["ts", "userid", "page", "method", "status"],
        "integer_columns": ["status", "userid", "registration"],
    },
}


def get_connection():
    return psycopg2.connect(
        host=os.getenv("STREAMIFY_PG_HOST", "localhost"),
        port=int(os.getenv("STREAMIFY_PG_PORT", "5433")),
        user=os.getenv("STREAMIFY_PG_USER", "streamify"),
        password=os.environ["STREAMIFY_PG_PASSWORD"],
        dbname=os.getenv("STREAMIFY_PG_DB", "streamify"),
    )


def load(event_type):
    config = CONFIG[event_type]

    df = ds.dataset(
        config["source_path"],
        format="parquet",
        partitioning="hive",
    ).to_table(columns=config["source_columns"]).to_pandas()

    df = df.rename(
        columns=dict(zip(config["source_columns"], config["db_columns"]))
    )

    for column, default in config["defaults"].items():
        df[column] = df[column].where(df[column].notna(), default)

    for column in config["integer_columns"]:
        df[column] = pd.to_numeric(df[column], errors="raise").astype("Int64")

    columns = config["db_columns"]

    # Convert timestamps to PostgreSQL-compatible strings for COPY.
    df["ts"] = pd.to_datetime(df["ts"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    buffer = io.StringIO()
    df[columns].to_csv(
        buffer,
        index=False,
        header=False,
        quoting=csv.QUOTE_MINIMAL,
        na_rep="",
    )
    buffer.seek(0)

    conn = get_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                staging_table = f"stage_{config['target_table']}"

                cur.execute(
                    f"""
                    CREATE TEMP TABLE {staging_table}
                    (LIKE {config['target_table']} INCLUDING DEFAULTS)
                    ON COMMIT DROP;
                    """
                )

                cur.copy_expert(
                    f"""
                    COPY {staging_table} ({", ".join(columns)})
                    FROM STDIN
                    WITH (FORMAT CSV)
                    """,
                    buffer,
                )

                key_conditions = " AND ".join(
                    f"t.{key} = s.{key}"
                    for key in config["key_columns"]
                )

                insert_sql = f"""
                    INSERT INTO {config['target_table']}
                    ({", ".join(columns)})
                    SELECT DISTINCT ON (
                        {", ".join(f"s.{key}" for key in config["key_columns"])}
                    )
                        {", ".join(f"s.{column}" for column in columns)}
                    FROM {staging_table} s
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM {config['target_table']} t
                        WHERE {key_conditions}
                    )
                    ORDER BY
                        {", ".join(f"s.{key}" for key in config["key_columns"])}
                    """

                cur.execute(insert_sql)
                inserted = cur.rowcount

        print(f"Event type: {event_type}")
        print(f"Parquet rows: {len(df)}")
        print(f"Rows inserted: {inserted}")
        print(f"Rows skipped as duplicates: {len(df) - inserted}")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Load Streamify Parquet events into PostgreSQL safely."
    )
    parser.add_argument(
        "event_type",
        choices=["listen", "page"],
        help="Event dataset to load.",
    )
    args = parser.parse_args()

    load(args.event_type)


if __name__ == "__main__":
    main()
