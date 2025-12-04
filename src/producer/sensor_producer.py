import time
import json
import random
import os
import logging
import sys
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker

# --- CONFIGURAÇÃO DE LOGS (PROFISSIONAL) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES GERAIS ---
BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC_NAME = 'sensores-iot'

CIDADES = [
    "São Paulo", "Rio de Janeiro", "Curitiba", "Belo Horizonte", 
    "Salvador", "Recife", "Porto Alegre", "Brasília"
]

fake = Faker()

def criar_produtor():
    try:
        logger.info(f"Tentando conectar ao Kafka em: {BOOTSTRAP_SERVERS}")
        producer = KafkaProducer(
            bootstrap_servers=[BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        logger.info("Conexão com Kafka estabelecida com sucesso!")
        return producer
    except Exception as e:
        logger.error(f"Falha ao conectar no Kafka: {e}")
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
    while producer is None:
        producer = criar_produtor()
        if producer is None:
            logger.warning("Kafka indisponível. Tentando novamente em 5 segundos...")
            time.sleep(5)

    logger.info(f"Iniciando simulação de sensores para o tópico: {TOPIC_NAME}")
    
    try:
        while True:
            dado = gerar_dado_sensor()
            producer.send(TOPIC_NAME, value=dado)
            # Log apenas INFO, limpo e com data automática
            logger.info(f"Enviado: {dado['cidade']} | {dado['temperatura']}°C | {dado['status']}")
            time.sleep(0.1) 
            
    except KeyboardInterrupt:
        logger.info("\n Parando o envio pelo usuário.")
        producer.close()
    except Exception as e:
        # exc_info=True mostra ONDE o erro aconteceu (linha do código)
        logger.error(f"Erro inesperado no loop de envio: {e}", exc_info=True)
    finally:
        if producer:
            producer.close()
            logger.info("Conexão com Kafka fechada.")

if __name__ == "__main__":
    iniciar_envio()