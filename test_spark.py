from pyspark.sql import SparkSession
spark = SparkSession.builder.master('local[*]').getOrCreate()
spark.range(5).write.mode('overwrite').parquet('/workspace/test_parquet')
