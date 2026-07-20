from __future__ import annotations

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, from_json, to_json, struct
from pyspark.sql.types import DoubleType, StringType, StructField, StructType, TimestampType

from spark.common.snowflake_sink import merge_slot_batch

SLOT_EVENT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), False),
        StructField("machine_id", StringType(), False),
        StructField("property_id", StringType(), False),
        StructField("event_time", TimestampType(), False),
        StructField("event_type", StringType(), False),
        StructField("coin_in", DoubleType(), True),
        StructField("payout", DoubleType(), True),
        StructField("jackpot_amount", DoubleType(), True),
        StructField("schema_version", StringType(), False),
    ]
)


def build_stream(spark: SparkSession):
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
        .option("subscribe", os.getenv("KAFKA_SLOT_TOPIC", "casino.slot.events.v1"))
        .option("startingOffsets", os.getenv("KAFKA_STARTING_OFFSETS", "latest"))
        .option("failOnDataLoss", "true")
        .load()
    )

    parsed = raw.select(
        from_json(col("value").cast("string"), SLOT_EVENT_SCHEMA).alias("event"),
        col("value").cast("string").alias("raw_payload"),
        col("topic"),
        col("partition"),
        col("offset"),
        col("timestamp").alias("broker_timestamp"),
    )

    valid = (
        parsed.where(col("event").isNotNull())
        .select("event.*", "topic", "partition", "offset", "broker_timestamp")
        .where(col("event_id").isNotNull() & col("machine_id").isNotNull())
        .withWatermark("event_time", os.getenv("SPARK_WATERMARK_DELAY", "10 minutes"))
        .dropDuplicates(["event_id"])
        .withColumn("payload", to_json(struct("event_id", "schema_version", "topic", "partition", "offset")))
        .withColumn("ingested_at", current_timestamp())
    )

    invalid = parsed.where(col("event").isNull()).select(
        "raw_payload", "topic", "partition", "offset", "broker_timestamp"
    )
    return valid, invalid


def main() -> None:
    spark = SparkSession.builder.appName("casino-slot-stream-v1").getOrCreate()
    spark.conf.set("spark.sql.shuffle.partitions", os.getenv("SPARK_SHUFFLE_PARTITIONS", "200"))
    valid, invalid = build_stream(spark)
    checkpoint_root = os.getenv("SPARK_CHECKPOINT_ROOT", "/tmp/casino-checkpoints")

    valid_query = (
        valid.writeStream.foreachBatch(merge_slot_batch)
        .option("checkpointLocation", f"{checkpoint_root}/slot-valid-v1")
        .trigger(processingTime=os.getenv("SPARK_TRIGGER_INTERVAL", "30 seconds"))
        .queryName("slot_events_to_snowflake")
        .start()
    )
    invalid_query = (
        invalid.selectExpr("CAST(offset AS STRING) AS key", "raw_payload AS value")
        .writeStream.format("kafka")
        .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
        .option("topic", os.getenv("KAFKA_SLOT_DLQ_TOPIC", "casino.slot.events.dlq.v1"))
        .option("checkpointLocation", f"{checkpoint_root}/slot-dlq-v1")
        .outputMode("append")
        .start()
    )
    spark.streams.awaitAnyTermination()
    valid_query.stop()
    invalid_query.stop()


if __name__ == "__main__":
    main()
