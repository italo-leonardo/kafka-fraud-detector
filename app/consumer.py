import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from confluent_kafka import Consumer, KafkaException, OFFSET_BEGINNING
import pymysql  # <- DRIVER COMPATÍVEL COM MySQL 8

# --- Configuração Kafka ---
conf = {
    'bootstrap.servers': 'localhost:9092',  # use localhost para conectar ao broker exposto pelo docker
    'group.id': 'fraud-detector-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}

consumer = Consumer(conf)
 
def on_assign(consumer, partitions):
    """Callback chamado ao atribuir partições — força leitura desde o início para novos grupos."""
    for p in partitions:
        p.offset = OFFSET_BEGINNING
    consumer.assign(partitions)

consumer.subscribe(['transactions'], on_assign=on_assign)

# --- Configuração Banco ---
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "kafka_fraud",
    "user": "app",
    "password": "app",
}

# Cria conexão com o banco
db = pymysql.connect(**DB_CONFIG)
cursor = db.cursor()

# Estruturas temporais para controle de regras
recent_tx = defaultdict(lambda: deque())
city_tx = defaultdict(lambda: deque())

print("Consumer iniciado. Aguardando mensagens...\n")

# --- Funções auxiliares ---

def parse_ts(ts):
    """Converte timestamp ISO8601 em datetime UTC"""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)

def save_transaction(ev):
    """Salva transação na tabela 'transactions'"""
    sql = """
        INSERT INTO transactions (event_id, client_id, city, amount, ts_utc)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        ev["event_id"],
        ev["client_id"],
        ev["city"],
        ev["amount"],
        parse_ts(ev["ts_utc"]).strftime("%Y-%m-%d %H:%M:%S")
    ))
    db.commit()

def save_alert(ev, rule, details):
    """Salva alerta de fraude na tabela 'alerts'"""
    sql = """
        INSERT INTO alerts (event_id, client_id, rule_code, details, ts_utc)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        ev["event_id"],
        ev["client_id"],
        rule,
        details,
        parse_ts(ev["ts_utc"]).strftime("%Y-%m-%d %H:%M:%S")
    ))
    db.commit()
    print(f"[ALERTA] {rule} | cliente={ev['client_id']} | valor={ev['amount']} | cidade={ev['city']} | {details}")

def check_rules(ev):
    """Aplica regras de detecção de fraude"""
    alerts = []
    client = ev["client_id"]
    city = ev["city"]
    amount = float(ev["amount"])
    ts = parse_ts(ev["ts_utc"])

    # 1️⃣ Regra: ALTO VALOR
    if amount >= 10000:
        alerts.append(("ALTO_VALOR", f"Valor alto: {amount:.2f}"))

    # 2️⃣ Regra: TEMPO_60s (4 transações em menos de 60s)
    recent_tx[client].append(ts)
    cutoff = ts - timedelta(seconds=60)
    while recent_tx[client] and recent_tx[client][0] < cutoff:
        recent_tx[client].popleft()
    if len(recent_tx[client]) >= 4:
        alerts.append(("TEMPO_60s", f"{len(recent_tx[client])} transações em <60s"))

    # 3️⃣ Regra: GEO_10m (2 cidades diferentes em 10min)
    city_tx[client].append((ts, city))
    cutoff2 = ts - timedelta(minutes=10)
    while city_tx[client] and city_tx[client][0][0] < cutoff2:
        city_tx[client].popleft()
    if len({c for _, c in city_tx[client]}) >= 2:
        alerts.append(("GEO_10m", f"Cidades distintas em 10m: {[c for _, c in city_tx[client]]}"))

    return alerts

# --- Loop principal ---
try:
    while True:
        msg = consumer.poll(timeout=2.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[ERRO KAFKA] {msg.error()}")
            continue

        # Decodifica a mensagem recebida
        value = msg.value().decode('utf-8')
        ev = json.loads(value)

        print(f"[RECEBIDA] {value}")  # Debug para ver mensagens no terminal

        # Salva transação e aplica regras
        save_transaction(ev)
        for rule, details in check_rules(ev):
            save_alert(ev, rule, details)

        # Confirma leitura no Kafka
        consumer.commit(asynchronous=False)

except KeyboardInterrupt:
    print("\nEncerrando consumer...")

finally:
    consumer.close()
    cursor.close()
    db.close()
