import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

from src import env_path


load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), env_path))


bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
topic_name = os.getenv("KAFKA_TOPIC_NAME")
sasl_usr = os.getenv("KAFKA_SASL_USERNAME")
sasl_pwd = os.getenv("KAFKA_SASL_PASSWORD")
group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "connectara-aiokafka-consumer")

assert all([bootstrap_servers, topic_name, sasl_usr, sasl_pwd]), "Missing required Kafka configuration in environment"

async def consume() -> None:
    if not all([bootstrap_servers, topic_name, sasl_usr, sasl_pwd]):
        raise RuntimeError("Missing required Kafka configuration in environment")

    consumer = AIOKafkaConsumer(
        topic_name,
        bootstrap_servers=bootstrap_servers, # type: ignore
        security_protocol="SASL_SSL",
        sasl_mechanism="PLAIN",
        sasl_plain_username=sasl_usr,
        sasl_plain_password=sasl_pwd,
        group_id=group_id,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    print(f"Connecting to cluster at {bootstrap_servers} ...")
    print(f"Subscribing to topic: {topic_name}")

    await consumer.start()
    try:
        i = 1
        async for msg in consumer:
            print("=" * 60)
            print(f"Message {i}")
            print(f"  Topic: {msg.topic}")
            print(f"  Partition: {msg.partition}")
            print(f"  Offset: {msg.offset}")
            print(f"  Key: {msg.key}")
            print(f"  Value: {msg.value}")
            i += 1
    except KeyboardInterrupt:
        print("\nStopping consumer (Ctrl+C pressed)...")
    finally:
        await consumer.stop()
        print("Consumer closed.")

def main() -> None:
    asyncio.run(consume())

if __name__ == "__main__":
    main()
