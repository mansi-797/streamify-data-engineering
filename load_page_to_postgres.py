from pyspark.sql import SparkSession 
from pyspark.sql.functions import coalesce, lit 
spark = SparkSession.builder.master("local[*]").getOrCreate() 
df = spark.read.parquet("streamify_data/page_view_events") 
df = df.select(df.ts, coalesce(df.page, lit("NA")).alias("page"), coalesce(df.auth, lit("NA")).alias("auth"), coalesce(df.method, lit("NA")).alias("method"), coalesce(df.status, lit(0)).alias("status"), coalesce(df.level, lit("NA")).alias("level"), coalesce(df.city, lit("NA")).alias("city"), coalesce(df.state, lit("NA")).alias("state"), coalesce(df.userAgent, lit("NA")).alias("userAgent"), coalesce(df.lon, lit(0.0)).alias("lon"), coalesce(df.lat, lit(0.0)).alias("lat"), coalesce(df.userId, lit(0)).alias("userId"), coalesce(df.lastName, lit("NA")).alias("lastName"), coalesce(df.firstName, lit("NA")).alias("firstName"), coalesce(df.gender, lit("NA")).alias("gender"), coalesce(df.registration, lit(9999999999999)).alias("registration"), coalesce(df.artist, lit("NA")).alias("artist"), coalesce(df.song, lit("NA")).alias("song"), coalesce(df.duration, lit(-1.0)).alias("duration")) 
jdbc_url = "jdbc:postgresql://host.docker.internal:5433/streamify" 
properties = {"user": "streamify", "password": "streamify", "driver": "org.postgresql.Driver"} 
jdbc_url = "jdbc:postgresql://host.docker.internal:5433/streamify" 
properties = {"user": "streamify", "password": "streamify", "driver": "org.postgresql.Driver"} 
df.write.mode("append").jdbc(url=jdbc_url, table="page_view_events", properties=properties) 
