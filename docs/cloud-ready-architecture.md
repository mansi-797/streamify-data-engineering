# Streamify — Cloud-Ready Architecture

## Purpose

Streamify is a fully implemented and tested local data engineering pipeline.
The project also contains a cloud-ready design for Google Cloud deployment.

The current project does not require a paid cloud account or live cloud resources.

## Local Architecture

EventSim
  ↓
Kafka
  ↓
Spark Structured Streaming
  ↓
Partitioned Parquet
  ↓
Airflow
  ↓
PostgreSQL staging
  ↓
dbt
  ↓
Dimension + Fact models
  ↓
dbt tests

## Cloud-Ready Architecture

EventSim
  ↓
Kafka
  ↓
Spark Structured Streaming
  ↓
Google Cloud Storage
  ↓
BigQuery staging
  ↓
dbt
  ↓
BigQuery analytical models
  ↓
Dashboard

A future cloud Airflow DAG will orchestrate this workflow.

## Component Mapping

| Local | Cloud-ready |
|---|---|
| Kafka | Managed Kafka or equivalent |
| Spark Structured Streaming | Managed Spark / Dataproc |
| Local Parquet | Google Cloud Storage |
| PostgreSQL staging | BigQuery staging |
| dbt-postgres | dbt-bigquery |
| Local Airflow | Managed or self-hosted Airflow |

## Storage Layout

listen_events/
  month=9/day=26/hour=13/*.parquet

page_view_events/
  month=9/day=26/hour=13/*.parquet

auth_events/
  month=9/day=26/hour=13/*.parquet

The same hourly partitioning can be preserved in cloud storage.

## BigQuery Staging

The cloud-ready staging dataset contains:

streamify_stg.listen_events
streamify_stg.page_view_events
streamify_stg.auth_events

Schema definitions:

setup/sql/bigquery/staging_schema.sql

## dbt

The project supports PostgreSQL locally and has been prepared for BigQuery.

BigQuery profile:

dbt/profiles.bigquery.yml.example

BigQuery-specific adaptations were made to:

- dim_users
- dim_datetime
- fact_streams

## Validation

The BigQuery dbt adapter is installed and the project successfully parses with
the BigQuery target configuration.

Live BigQuery execution has not been performed.

Therefore, this is a cloud-ready architecture, not a currently deployed
production cloud pipeline.

## Future Deployment

1. Provision Google Cloud resources.
2. Configure Kafka and Spark.
3. Configure the GCS bucket.
4. Run Spark with the GCS output path.
5. Load BigQuery staging tables.
6. Configure dbt-bigquery.
7. Deploy the cloud Airflow DAG.
8. Run dbt transformations and tests.
9. Connect the analytical models to a dashboard.
