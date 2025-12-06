from confluent_kafka import Consumer, TopicPartition
import os, json
from dotenv import load_dotenv

from src import env_path

load_dotenv(env_path)

# Kafka Configuration
bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
topic_name = os.getenv("KAFKA_TOPIC_NAME")
sasl_usr = os.getenv("KAFKA_SASL_USERNAME")
sasl_pwd = os.getenv("KAFKA_SASL_PASSWORD")

group_id = "team-cg-a373170e68e54c97b4fcc2249f51a009"

def get_next_message():
    """
    Generator that yields decoded JSON values from Kafka.
    Starts from the latest offset (skips old messages) and tails for new messages.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": sasl_usr,
        "sasl.password": sasl_pwd,
        "group.id": group_id,
        "enable.auto.commit": True,
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(conf)

    try:
        print(f"Connecting to cluster at {bootstrap_servers} ...")

        # Fetch metadata so we know partitions
        md = consumer.list_topics(topic_name, timeout=10)
        if topic_name not in md.topics:
            print(f"Topic {topic_name} not found in cluster.")
            return

        topic_md = md.topics[topic_name]
        partitions = list(topic_md.partitions.keys())
        print(f"Topic {topic_name} has partitions: {partitions}")

        # Get actual low watermarks and assign from there
        tps_for_watermark = [TopicPartition(topic_name, p) for p in partitions]
        tps_with_offset = []
        
        print("Partition watermarks (low_offset, high_offset):")
        for tp in tps_for_watermark:
            low, high = consumer.get_watermark_offsets(tp, timeout=5)
            print(
                f"  partition={tp.partition}: low={low}, high={high} "
                "(high is next offset to be written)"
            )
            # Assign from the high watermark (latest) to skip old messages
            tps_with_offset.append(TopicPartition(topic_name, tp.partition, high))
        
        consumer.assign(tps_with_offset)
        
        print("\nAssigned partitions from latest offset (skipping old messages):")
        for tp in tps_with_offset:
            print(f"  topic={tp.topic}, partition={tp.partition}, offset={tp.offset}")

        print("\nWaiting for new messages...")
        print("(Ctrl+C to stop)\n")

        while True:
            msg = consumer.poll(2.0)
            if msg is None:
                # No new messages right now; just keep tailing
                continue

            if msg.error():
                print("Error:", msg.error())
                continue

            print("=" * 60)
            print(f"Partition: {msg.partition()}  Offset: {msg.offset()}")
            key = msg.key()
            if key is not None:
                try:
                    print("Key:", key.decode("utf-8"))
                except Exception:
                    print("Key (raw):", key)
            else:
                print("Key: None")

            val = msg.value()
            try:
                as_str = val.decode("utf-8")
                print("Value (utf-8):", as_str)
                try:
                    yield json.loads(as_str)
                except json.JSONDecodeError:
                    continue #we expect all valid messages to be JSON
            except Exception as e:
                print("Value decode error:", e)

    except KeyboardInterrupt:
        print("\nStopping consumer (Ctrl+C pressed)...")
    finally:
        consumer.close()
        print("Consumer closed.")

def main():
    """Example usage of the generator - iterates through all messages and prints them"""
    message_count = 0
    try:
        for message in get_next_message():
            message_count += 1
            print(f"\n[Message #{message_count}]")
            
            # Try to parse as JSON and pretty print
            try:
                as_json = json.loads(message)
                print(json.dumps(as_json, indent=2))
            except json.JSONDecodeError:
                print(message)
                
    except KeyboardInterrupt:
        print(f"\n\nStopped after processing {message_count} messages.")


if __name__ == "__main__":
    # main()
    pass
