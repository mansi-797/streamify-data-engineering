import os
from streaming_functions_local import *
from schema import schema

# Kafka Topics
LISTEN_EVENTS_TOPIC = "listen_events"
PAGE_VIEW_EVENTS_TOPIC = "page_view_events"
AUTH_EVENTS_TOPIC = "auth_events"

# Kafka inside Docker network
KAFKA_PORT = os.getenv("KAFKA_PORT", "9092")
KAFKA_ADDRESS = os.getenv("KAFKA_ADDRESS", "localhost")

# Local storage inside the Spark Docker container
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./streamify_data")

# Initialize a Spark session
spark = create_or_get_spark_session("Eventsim Stream", master="local[*]")

# Listen events stream
listen_events = create_kafka_read_stream(
    spark,
    KAFKA_ADDRESS,
    KAFKA_PORT,
    LISTEN_EVENTS_TOPIC
)

listen_events = process_stream(
    listen_events,
    schema[LISTEN_EVENTS_TOPIC],
    LISTEN_EVENTS_TOPIC
)

# Page view stream
page_view_events = create_kafka_read_stream(
    spark,
    KAFKA_ADDRESS,
    KAFKA_PORT,
    PAGE_VIEW_EVENTS_TOPIC
)

page_view_events = process_stream(
    page_view_events,
    schema[PAGE_VIEW_EVENTS_TOPIC],
    PAGE_VIEW_EVENTS_TOPIC
)

# Auth stream
auth_events = create_kafka_read_stream(
    spark,
    KAFKA_ADDRESS,
    KAFKA_PORT,
    AUTH_EVENTS_TOPIC
)

auth_events = process_stream(
    auth_events,
    schema[AUTH_EVENTS_TOPIC],
    AUTH_EVENTS_TOPIC
)

# Write processed events to local Parquet storage
# Every 2 minutes, partitioned by month/day/hour

listen_events_writer = create_file_write_stream(
    listen_events,
    f"{LOCAL_STORAGE_PATH}/{LISTEN_EVENTS_TOPIC}",
    f"{LOCAL_STORAGE_PATH}/checkpoint/{LISTEN_EVENTS_TOPIC}"
)

page_view_events_writer = create_file_write_stream(
    page_view_events,
    f"{LOCAL_STORAGE_PATH}/{PAGE_VIEW_EVENTS_TOPIC}",
    f"{LOCAL_STORAGE_PATH}/checkpoint/{PAGE_VIEW_EVENTS_TOPIC}"
)

auth_events_writer = create_file_write_stream(
    auth_events,
    f"{LOCAL_STORAGE_PATH}/{AUTH_EVENTS_TOPIC}",
    f"{LOCAL_STORAGE_PATH}/checkpoint/{AUTH_EVENTS_TOPIC}"
)

# Start all three streaming queries
listen_events_writer.start()
auth_events_writer.start()
page_view_events_writer.start()

# Keep the streaming application running
spark.streams.awaitAnyTermination()