from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("KafkaTest").getOrCreate()

df = spark.read.format("kafka").option("kafka.bootstrap.servers", "broker:29092").option("subscribe", "page_view_events").option("startingOffsets", "earliest").load()

df.selectExpr("CAST(value AS STRING) AS event").show(5, truncate=False)

spark.stop()
