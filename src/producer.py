from kafka import KafkaProducer
import json
import os

# Kafka Configuration

# Initialize Producer
producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers.split(','),
    security_protocol='SASL_SSL',
    sasl_mechanism='PLAIN',
    sasl_plain_username=sasl_usr,
    sasl_plain_password=sasl_pwd,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
)

# Sample event
event = {
    "event": "connectara_test",
    "data": {
        "message": "Hello from producer.py",
    },
}

def main() -> None:
    print(f"Sending event to topic: {topic_name}")
    try:
        for _ in range(50) :
            future = producer.send(topic_name, value=event)
            record_metadata = future.get(timeout=10)
            print("Message sent successfully")
            print(f"Topic: {record_metadata.topic}")
            print(f"Partition: {record_metadata.partition}")
            print(f"Offset: {record_metadata.offset}")
    except Exception as e:
        print(f"Error sending message: {e}")
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    main()