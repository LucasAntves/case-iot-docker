import time
import json
import random
import os
from kafka import KafkaProducer
from faker import Faker
from datetime import datetime

# --- CONFIGURAÇÕES DINÂMICAS ---
# Pega do Docker ou usa localhost se não encontrar
BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC_NAME = 'sensores-iot'

# lista de Cidades
CIDADES = ["São Paulo", "Rio de Janeiro", "Curitiba", "Belo Horizonte", "Salvador", "Recife"]

fake = Faker()

def criar_produtor():
    try:
        print(f"Tentando conectar ao Kafka em: {BOOTSTRAP_SERVERS}")
        producer = KafkaProducer(
            bootstrap_servers=[BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        print("Conexão com Kafka estabelecida!")
        return producer
    except Exception as e:
        print(f"Erro ao conectar no Kafka: {e}")
        return None

def gerar_dado_sensor():
    return {
        "sensor_id": random.randint(1, 50),
        "temperatura": round(random.uniform(20.0, 45.0), 2),
        "umidade": round(random.uniform(30.0, 90.0), 2),
        "data_hora": datetime.now().isoformat(),
        "cidade": random.choice(CIDADES),
        "status": random.choice(["OK", "ALERTA", "CRITICO"])
    }

def iniciar_envio():
    producer = None
    # Tentativa de reconexão simples (caso o Kafka demore a subir)
    while producer is None:
        producer = criar_produtor()
        if producer is None:
            print("Kafka indisponível. Tentando novamente em 5 segundos...")
            time.sleep(5)

    print(f"Iniciando simulação de sensores para o tópico: {TOPIC_NAME}")
    
    try:
        while True:
            dado = gerar_dado_sensor()
            producer.send(TOPIC_NAME, value=dado)
            print(f"Enviado: {dado}")
            time.sleep(2) # Envia a cada 2 segundos
            
    except KeyboardInterrupt:
        print("\n Parando o envio...")
        producer.close()

if __name__ == "__main__":
    iniciar_envio() 