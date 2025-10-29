import json
import random
import time
import uuid
from datetime import datetime, timezone
from confluent_kafka import Producer

# --- Configuração do Producer ---
conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

CITIES = ["Crato", "Juazeiro", "Fortaleza", "Sobral", "Iguatu"]
CLIENTS = [f"CLI_{i:03d}" for i in range(1, 3)]

def now_utc_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def build_transaction():
    """Gera uma transação simulada"""
    return {
        "event_id": str(uuid.uuid4()),
        "client_id": random.choice(CLIENTS),
        "city": random.choice(CITIES),
        "amount": round(random.uniform(10, 20000), 2),
        "ts_utc": now_utc_iso()
    }

def delivery_report(err, msg):
    """Callback para confirmar entrega"""
    if err is not None:
        print(f"Falha ao entregar mensagem: {err}")
    else:
        print(f"[ENVIADA] para {msg.topic()} [partição {msg.partition()}] -> {msg.value().decode('utf-8')}")

print("Producer iniciado. Enviando transações a cada 3 segundos...")

while True:
    tx = build_transaction()
    key = tx["client_id"]
    producer.produce(
        topic="transactions",
        key=key,
        value=json.dumps(tx),
        callback=delivery_report
    )
    producer.flush()
    time.sleep(3)
