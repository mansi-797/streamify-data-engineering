from pyspark.sql import SparkSession 
spark = SparkSession.builder.master("local[*]").getOrCreate() 
df = spark.read.parquet("streamify_data/page_view_events") 
df.printSchema() 
